# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from functools import partial

import colander
import inspect
import six
from webob.multidict import MultiDict


LISTING_CONF = {
    'max_limit': 500
}


class AllowEmptyMeta(colander._SchemaMeta):

    def __new__(mcs, classname, superclasses, attrdict):

        # Create new schema type with extended methods
        origin_node_type_class = attrdict.get('schema_type')
        if not origin_node_type_class:
            ValueError('schema_type attribute is not specified')

        def schema_type_init_func(self, *args, **kwargs):
            self.allow_empty = kwargs.pop('allow_empty', False)
            super(self.__class__, self).__init__(*args, **kwargs)

        def serialize_func(self, node, appstruct):
            if self.allow_empty and appstruct is None:
                return appstruct
            return super(self.__class__, self).serialize(node, appstruct)

        def deserialize_func(self, node, cstruct):
            if (cstruct == '' or cstruct is None) and self.allow_empty:
                return None
            return super(self.__class__, self).deserialize(node, cstruct)

        AllowEmptyNodeType = type(
            origin_node_type_class.__name__ + 'AllowEmpty',
            (origin_node_type_class,),
            {'__init__': schema_type_init_func, 'serialize': serialize_func, 'deserialize': deserialize_func}
        )

        # Extend methods of node
        arg_spec = None
        if origin_node_type_class.__init__ is not object.__init__:
            arg_spec = inspect.getargspec(origin_node_type_class.__init__)

        def init_func(self, *args, **kwargs):
            self.node_type_args = {
                'allow_empty': kwargs.pop('allow_empty', False)
            }
            if arg_spec:
                for arg in arg_spec.args[1:]:
                    if arg in kwargs:
                        self.node_type_args[arg] = kwargs.pop(arg)

            super(self.__class__, self).__init__(*args, **kwargs)

        def schema_type_func(self):
            return AllowEmptyNodeType(**self.node_type_args)

        attrdict['__init__'] = init_func
        attrdict['schema_type'] = schema_type_func

        return super(AllowEmptyMeta, mcs).__new__(mcs, classname, superclasses, attrdict)


# Schema types

class EmptyString(colander.String):

    def __init__(self, encoding=None):
        super(EmptyString, self).__init__(encoding=encoding, allow_empty=True)


class UrlEncodeMapping(colander.Mapping):
    """Adding support of MultiDict as input value."""

    def _validate(self, node, value):
        if isinstance(value, MultiDict):
            new_value = {}
            for sub_node in node.children:
                name = sub_node.name
                if name not in value:
                    continue
                new_value[name] = value.getall(name) if isinstance(sub_node.typ, colander.Sequence) else value[name]
            return new_value
        return super(UrlEncodeMapping, self)._validate(node, value)


# Basic nodes


class MappingSchema(colander.SchemaNode):
    """Use this class instead of colander.MappingSchema
    to support urlencoded input data represented as instance of MultiDict."""
    schema_type = UrlEncodeMapping


class StringNode(colander.SchemaNode):
    schema_type = colander.String

    def __init__(self, *args, **kwargs):
        self.strip = kwargs.pop('strip', True)
        super(StringNode, self).__init__(*args, **kwargs)

    def preparer(self, appstruct):
        if appstruct is colander.null:
            return appstruct
        if self.strip:
            appstruct = appstruct.strip()
        return appstruct or colander.null


class EmptyStringNode(colander.SchemaNode):
    schema_type = EmptyString

    def __init__(self, *args, **kwargs):
        self.strip = kwargs.pop('strip', True)
        super(EmptyStringNode, self).__init__(*args, **kwargs)

    def preparer(self, appstruct):
        if appstruct is colander.null:
            return appstruct
        if self.strip:
            appstruct = appstruct.strip()
        return appstruct


class IntegerNode(colander.SchemaNode):
    __metaclass__ = AllowEmptyMeta
    schema_type = colander.Integer


class UnsignedIntegerNode(colander.SchemaNode):
    schema_type = colander.Integer
    validator = colander.Range(min=0)


class FloatNode(colander.SchemaNode):
    schema_type = colander.Float


class MoneyNode(colander.SchemaNode):
    schema_type = colander.Money


class BooleanNode(colander.SchemaNode):
    schema_type = colander.Boolean


class DateTimeNode(colander.SchemaNode):
    __metaclass__ = AllowEmptyMeta
    schema_type = colander.DateTime


class DateNode(colander.SchemaNode):
    __metaclass__ = AllowEmptyMeta
    schema_type = colander.Date


class EmailNode(colander.SchemaNode):
    title = 'Email'
    schema_type = colander.String
    validator = colander.All(colander.Length(max=250), colander.Email())


class EmbeddedNode(colander.SchemaNode):
    schema_type = colander.Mapping
    title = 'Embedded resources'

    def _bind(self, kw):
        kw = kw.copy()
        kw['is_embedded'] = True
        return super(EmbeddedNode, self)._bind(kw)


class SequenceNode(colander.SequenceSchema):

    def __init__(self, *args, **kwargs):
        self.accept_scalar = kwargs.pop('accept_scalar', False)
        super(SequenceNode, self).__init__(*args, **kwargs)

    def schema_type(self):
        return colander.Sequence(accept_scalar=self.accept_scalar)


class MappingNode(colander.MappingSchema):

    def __init__(self, *args, **kwargs):
        self.unknown = kwargs.pop('unknown', 'ignore')
        super(MappingNode, self).__init__(*args, **kwargs)

    def schema_type(self):
        return colander.Mapping(unknown=self.unknown)


# Validators

class LaconicOneOf(colander.OneOf):
    """Laconic version of standard OneOf validator."""

    def __call__(self, node, value):
        if value not in self.choices:
            err = colander._('"${val}" is not one of allowed values',
                             mapping={'val': value})
            raise colander.Invalid(node, err)


class LaconicNoneOf(colander.OneOf):
    """Laconic version of standard NoneOf validator."""

    def __call__(self, node, value):
        if value in self.choices:
            err = colander._('"${val}" is not allowed value',
                             mapping={'val': value})
            raise colander.Invalid(node, err)


# Schemas

class GetResourceSchema(MappingSchema):
    pass


class ResourceSchema(colander.MappingSchema):
    pass


# HAL Schemas

class HalLinkNode(colander.MappingSchema):
    href = colander.SchemaNode(colander.String(), title='URL to a resource',
                               validator=colander.url)
    templated = colander.SchemaNode(colander.Boolean(), title='URL is templated',
                                    default=False, missing=colander.drop)


class HalLinksSchema(colander.MappingSchema):
    title = 'HAL links'
    self = HalLinkNode(title='Link to this resource')

    def after_bind(self, node, kw):
        """Add links to sub-resources.
        :type node: colander.SchemaNode
        :type kw: dict
        """
        if kw.get('is_embedded', False):
            # Do not add links to sub-resources into schema of embedded resource.
            # Because current ``context`` is not an embedded resource.
            return
        request = kw.get('request')
        context = kw.get('context')
        if not request or not context:
            return
        for name, _ in context.get_sub_resources(request.registry):
            if name and not node.get(name):
                child = HalLinkNode(name=name, title='Link to {}'.format(name)).bind(**kw)
                node.add(child)


class DynamicHalLinksNode(colander.SchemaNode):
    title = 'HAL links'
    schema_type = partial(colander.Mapping, unknown='preserve')

    @staticmethod
    def validator(node, mapping):
        link_node = HalLinkNode()
        for value in mapping.values():
            link_node.deserialize(value)


class PagesHalLinksSchema(HalLinksSchema):
    next = HalLinkNode(title='Link to the next page of list of embedded resources', missing=colander.drop)
    prev = HalLinkNode(title='Link to the previous page of list of embedded resources', missing=colander.drop)


class HalResourceSchema(colander.MappingSchema):
    _links = HalLinksSchema()


def missing_limit():
    return LISTING_CONF['max_limit']


def prepare_limit(value):
    if not value:
        return LISTING_CONF['max_limit']
    return min(value, LISTING_CONF['max_limit'])


class GetEmbeddedSchema(GetResourceSchema):
    """This schema can be used to get pagination parameters."""
    embedded = colander.SchemaNode(colander.Boolean(), title='Include an embedded resources',
                                   missing=True)
    offset = colander.SchemaNode(colander.Integer(), title='Offset',
                                 description='Offset from the start of children resources.',
                                 default=0, missing=0,
                                 validator=colander.Range(min=0))
    limit = colander.SchemaNode(colander.Integer(), title='Limit',
                                preparer=prepare_limit, missing=missing_limit,
                                validator=colander.Range(min=0))
    total_count = colander.SchemaNode(colander.Boolean(), title='Calculate total count',
                                      missing=False)


class EmbeddedItemsSchema(colander.MappingSchema):
    items = colander.SchemaNode(colander.List(), title='List of items',
                                missing=colander.drop)


class HalResourceWithEmbeddedSchema(HalResourceSchema):
    _links = PagesHalLinksSchema()
    _embedded = EmbeddedItemsSchema(title='Embedded list of items',
                                    default=colander.drop)


_undefined = object()


def clone_schema_class(name, base_schema, only=None, excludes=None,
                       nodes_missing=_undefined, replace_validators=None, **kwargs):
    """
    :type name: string
    :type base_schema: colander.SchemaNode or colander._SchemaNode
    :type only: list of objects
    :type excludes: list of objects
    :type nodes_missing: object
    :type replace_validators: dict
    :rtype: colander.SchemaNode
    """
    cloned_schema = type(name, (base_schema,), kwargs)
    all_schema_nodes = base_schema.__all_schema_nodes__[:]
    all_schema_nodes.extend(cloned_schema.__class_schema_nodes__)
    node_by_name = {node.name: node for node in all_schema_nodes}
    excludes = excludes or []
    for exclude in excludes:
        if isinstance(exclude, six.string_types):
            if exclude in node_by_name:
                all_schema_nodes.remove(node_by_name[exclude])
                del node_by_name[exclude]
        elif issubclass(exclude, colander.SchemaNode):
            for node in exclude.__all_schema_nodes__:
                if node.name in node_by_name:
                    all_schema_nodes.remove(node_by_name[node.name])
                    del node_by_name[node.name]

    only = set(only or [])
    if only:
        for name, node in node_by_name.items():
            if name not in only and name not in kwargs:
                all_schema_nodes.remove(node)

    replace_validators = replace_validators or {}
    changed_schema_nodes = []
    for node in all_schema_nodes:
        new_node = node.clone()
        if nodes_missing is not _undefined:
            new_node.missing = nodes_missing
        new_node.validator = replace_validators.get(new_node.name, new_node.validator)
        changed_schema_nodes.append(new_node)
    cloned_schema.__all_schema_nodes__ = changed_schema_nodes
    return cloned_schema
