# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from functools import partial
from urllib.parse import urlsplit

import colander
from pyramid.interfaces import ILocation
from pyramid.traversal import find_resource
from webob.multidict import MultiDict
from zope.interface.interfaces import IInterface

from .external_links import get_external_links


LISTING_CONF = {
    'max_limit': 500
}


# Schema types

class Nullable(colander.SchemaType):
    """A type which accepts serialize None to None and deserialize ''/None to None.
    When the value is not equal to None/'', it will use (de)serialization of
    the given type. This can be used to make nodes optional.

    Example:

      .. code-block:: python

        time = colander.SchemaNode(
            Nullable(colander.DateTime()),
            default=colander.drop,
            missing=colander.drop,
        )
    """

    def __init__(self, typ, null_values=None):
        self.typ = typ
        self.null_values = null_values if null_values is not None else ['']

    def serialize(self, node, appstruct):
        if appstruct is None:
            return appstruct
        return self.typ.serialize(node, appstruct)

    def deserialize(self, node, cstruct):
        if cstruct is None or cstruct in self.null_values:
            return None
        return self.typ.deserialize(node, cstruct)


class NullableValidator(object):

    def __init__(self, validator):
        self.validator = validator

    def __call__(self, node, value):
        if value is not None:
            return self.validator(node, value)


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


class PreserveMappingSchema(colander.MappingSchema):
    def schema_type(self):
        return UrlEncodeMapping(unknown='preserve')


class BaseNode(colander.SchemaNode):

    def __init__(self, *args, **kwargs):
        nullable = kwargs.pop('nullable', False)
        if nullable:
            schema_type = self.schema_type
            self.schema_type = lambda: Nullable(schema_type())
        super(BaseNode, self).__init__(*args, **kwargs)
        if nullable and self.validator is not None:
            self.validator = NullableValidator(self.validator)


class StringNode(BaseNode):
    schema_type = colander.String

    def __init__(self, *args, **kwargs):
        self.strip = kwargs.pop('strip', True)
        super(StringNode, self).__init__(*args, **kwargs)

    def preparer(self, appstruct):
        if appstruct is colander.null or appstruct is None:
            return appstruct
        if self.strip and appstruct:
            appstruct = appstruct.strip()
        return appstruct or colander.null


class EmptyStringNode(colander.SchemaNode):
    schema_type = EmptyString

    def __init__(self, *args, **kwargs):
        self.strip = kwargs.pop('strip', True)
        nullable = kwargs.pop('nullable', False)
        if nullable:
            schema_type = self.schema_type
            self.schema_type = lambda: Nullable(schema_type(), null_values=[])
        super(EmptyStringNode, self).__init__(*args, **kwargs)

    def preparer(self, appstruct):
        if appstruct is colander.null or appstruct is None:
            return appstruct
        if self.strip and appstruct:
            appstruct = appstruct.strip()
        return appstruct


class IntegerNode(BaseNode):
    schema_type = colander.Integer

    def __init__(self, *args, **kwargs):
        if kwargs.pop('allow_empty', False):
            kwargs['nullable'] = True
        super(IntegerNode, self).__init__(*args, **kwargs)


class UnsignedIntegerNode(BaseNode):
    schema_type = colander.Integer
    validator = colander.Range(min=0)


class FloatNode(BaseNode):
    schema_type = colander.Float


class MoneyNode(BaseNode):
    schema_type = colander.Money


class BooleanNode(BaseNode):
    schema_type = colander.Boolean


class DateTimeNode(BaseNode):

    def __init__(self, *args, default_tzinfo=None, dt_format=None, **kwargs):
        if kwargs.pop('allow_empty', False):
            kwargs['nullable'] = True
        self.default_tzinfo = default_tzinfo
        self.dt_format = dt_format
        super(DateTimeNode, self).__init__(*args, **kwargs)

    def schema_type(self):
        return colander.DateTime(
            default_tzinfo=self.default_tzinfo,
            format=self.dt_format,
        )


class DateNode(BaseNode):
    schema_type = colander.Date

    def __init__(self, *args, **kwargs):
        if kwargs.pop('allow_empty', False):
            kwargs['nullable'] = True
        super(DateNode, self).__init__(*args, **kwargs)


class EmailNode(BaseNode):
    title = 'Email'
    schema_type = colander.String
    validator = colander.All(colander.Length(max=250), colander.Email())


class EmbeddedNode(BaseNode):
    schema_type = colander.Mapping
    title = 'Embedded resources'

    def _bind(self, kw):
        kw = kw.copy()
        kw['is_embedded'] = True
        return super(EmbeddedNode, self)._bind(kw)


class SequenceNode(BaseNode, colander.SequenceSchema):

    def __init__(self, *args, **kwargs):
        self.accept_scalar = kwargs.pop('accept_scalar', False)
        super(SequenceNode, self).__init__(*args, **kwargs)

    def schema_type(self):
        return colander.Sequence(accept_scalar=self.accept_scalar)


class MappingNode(BaseNode, colander.MappingSchema):

    def __init__(self, *args, **kwargs):
        self.unknown = kwargs.pop('unknown', 'ignore')
        super(MappingNode, self).__init__(*args, **kwargs)

    def schema_type(self):
        return colander.Mapping(unknown=self.unknown)


class ResourceNode(BaseNode):
    schema_type = ResourceType


# Validators

class LazyAll(object):
    """Composite validator which fail if one of its
    subvalidators raises an :class:`colander.Invalid` exception"""

    def __init__(self, *validators):
        self.validators = validators

    def __call__(self, node, value):
        for validator in self.validators:
            validator(node, value)


class LazyAny(object):
    """Composite validator which fail if all of its
    subvalidators raises an :class:`colander.Invalid` exception"""

    def __init__(self, *validators):
        self.validators = validators

    def __call__(self, node, value):
        errors = []
        for validator in self.validators:
            try:
                validator(node, value)
                return
            except colander.Invalid as e:
                errors.append(e)
        if errors:
            exc = colander.Invalid(node, [exc.msg for exc in errors])
            for e in errors:
                exc.children.extend(e.children)
            raise exc


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
    href = StringNode(title='URL to a resource', validator=colander.url)
    templated = BooleanNode(title='URL is templated', missing=colander.drop)


class HalLinksSchema(colander.MappingSchema):
    title = 'HAL links'
    self = HalLinkNode(title='Link to this resource')

    def after_bind(self, node, kw):
        """Add external links and links to sub-resources
        :type node: colander.SchemaNode
        :type kw: dict
        """
        if kw.get('is_embedded', False):
            # Do not add external links and links to sub-resources into schema
            # of embedded resource. Because current ``context`` is not
            # an embedded resource.
            return
        request = kw.get('request')
        context = kw.get('context')
        if not request or not context:
            return

        for name, link_fabric in get_external_links(context, request.registry):
            if name and not node.get(name):
                missing = colander.drop if link_fabric.optional else colander.required
                title = link_fabric.title or ('Link to %s' % name)
                child = HalLinkNode(
                    name=name,
                    title=title,
                    description=link_fabric.description,
                    missing=missing,
                ).bind(**kw)
                node.add(child)

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
    next = HalLinkNode(
        title='Next page',
        description='Link to the next page of list of embedded resources',
        missing=colander.drop,
    )
    prev = HalLinkNode(
        title='Previous page',
        description='Link to the previous page of list of embedded resources',
        missing=colander.drop,
    )


class HalResourceSchema(colander.MappingSchema):
    _links = HalLinksSchema()


def missing_limit():
    return LISTING_CONF['max_limit']


def prepare_limit(value):
    if not value:
        return LISTING_CONF['max_limit']
    return min(value, LISTING_CONF['max_limit'])


class GetEmbeddedSchema(GetResourceSchema):
    """This schema can be used to get pagination parameters based on offset of page start."""
    embedded = BooleanNode(title='Include an embedded resources', missing=True)
    offset = IntegerNode(
        title='Offset',
        description='Offset from the start of children resources.',
        default=0, missing=0,
        validator=colander.Range(min=0),
    )
    limit = IntegerNode(
        title='Limit',
        preparer=prepare_limit, missing=missing_limit,
        validator=colander.Range(min=0),
    )
    total_count = BooleanNode(title='Calculate total count', missing=False)


class GetNextPageSchema(GetResourceSchema):
    """This schema can be used to get pagination parameters based on 'cursor' position."""
    embedded = BooleanNode(title='Include an embedded resources', missing=True)
    cursor_next = StringNode(
        title='Next item position', missing='',
        description='Position of next item used for listing in forward direction.'
    )
    limit = IntegerNode(
        title='Limit',
        preparer=prepare_limit, missing=missing_limit,
        validator=colander.Range(min=0),
    )
    total_count = BooleanNode(title='Calculate total count', missing=False)


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
        if isinstance(exclude, str):
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
        for node_name, node in node_by_name.items():
            if node_name not in only and node_name not in kwargs:
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
