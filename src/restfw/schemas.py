# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from functools import partial

import colander
import six
from pyramid.interfaces import ILocation
from pyramid.traversal import find_resource
from six.moves.urllib_parse import urlsplit
from webob.multidict import MultiDict
from zope.interface.interfaces import IInterface


LISTING_CONF = {
    'max_limit': 500
}


class Nullable(colander.SchemaType):
    """A type which accepts serialize None to None and deserialize ''/None to None.
    When the value is not equal to None/'', it will use (de)serialization of
    the given type. This can be used to make nodes optional.
    Example:
        date = colander.SchemaNode(
            colander.NoneType(colander.DateTime()),
            default=None,
            missing=None,
        )
    """

    def __init__(self, typ):
        self.typ = typ

    def serialize(self, node, appstruct):
        if appstruct is None:
            return appstruct

        return self.typ.serialize(node, appstruct)

    def deserialize(self, node, cstruct):
        if cstruct == '' or cstruct is None:
            return None

        return self.typ.deserialize(node, cstruct)


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


class ResourceType(colander.SchemaType):
    """A type representing a resource object that supports ``ILocation`` interface."""

    def serialize(self, node, appstruct):
        if not appstruct:
            return colander.null
        if not ILocation.providedBy(appstruct):
            raise colander.Invalid(node, colander._('"${val}" object has not provide ILocation',
                                                    mapping={'val': appstruct}))
        bindings = node.bindings or {}
        request = bindings.get('request', None)
        if not request:
            raise RuntimeError('"request" has not found inside of schema node bindings')
        return request.resource_url(appstruct)

    def deserialize(self, node, cstruct):
        if not cstruct:
            return colander.null
        bindings = node.bindings or {}
        request = bindings.get('request', None)
        if not request:
            raise RuntimeError('"request" has not found inside of schema node bindings')

        resource_path = urlsplit(cstruct).path
        try:
            resource = find_resource(request.root, resource_path)
        except KeyError:
            raise colander.Invalid(node, colander._('Resource has not found'))
        return resource


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
    schema_type = colander.Integer

    def __init__(self, *args, **kwargs):
        if kwargs.pop('allow_empty', False):
            schema_type = self.schema_type
            self.schema_type = lambda: Nullable(schema_type())
        super(IntegerNode, self).__init__(*args, **kwargs)


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
    schema_type = colander.DateTime

    def __init__(self, *args, **kwargs):
        if kwargs.pop('allow_empty', False):
            schema_type = self.schema_type
            self.schema_type = lambda: Nullable(schema_type())
        super(DateTimeNode, self).__init__(*args, **kwargs)


class DateNode(colander.SchemaNode):
    schema_type = colander.Date

    def __init__(self, *args, **kwargs):
        if kwargs.pop('allow_empty', False):
            schema_type = self.schema_type
            self.schema_type = lambda: Nullable(schema_type())
        super(DateNode, self).__init__(*args, **kwargs)


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


class ResourceNode(colander.SchemaNode):
    schema_type = ResourceType


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


class ResourceInterface(object):
    """Validator which succeeds if the type or interface of value passed to it
    is one of a fixed set of interfaces and classes."""

    def __init__(self, interface, *interfaces):
        """
        :param interface: interface or class of resource
        :param interfaces: addition interfaces or classes of resource
        """
        self.interfaces = set(interfaces)
        self.interfaces.add(interface)
        self._validators = []
        for class_or_interface in self.interfaces:
            if IInterface.providedBy(class_or_interface):
                self._validators.append(class_or_interface.providedBy)
            else:
                self._validators.append(lambda arg: isinstance(arg, class_or_interface))

    def __call__(self, node, value):
        if not any(v(value) for v in self._validators):
            choices = ', '.join(x.__name__ for x in self.interfaces)
            err = colander._('Type of "${val}" is not one of ${choices}',
                             mapping={'val': value, 'choices': choices})
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
