# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 28.04.2015
"""

from collections import OrderedDict
from functools import partial

import colander
import colander.interfaces

from restfw.renderers import build_json_renderer
from .. import schemas


_JSON_SERIALIZER = partial(
    build_json_renderer(indent=2, ensure_ascii=False)(None), system={}
)


def colander_2_json_schema(schema_class, request, context, serializer=_JSON_SERIALIZER):
    """Serialize colander schema into JSON Schema string.
    :type schema_class: colander.SchemaNode
    :type request: pyramid.interfaces.IRequest
    :type context: restfw.interfaces.IResource
    :param serializer:
    :rtype: str or None
    """
    if schema_class is None:
        return None
    bound_schema = schema_class().bind(request=request, context=context)
    json_schema = convert(bound_schema)
    json_schema = serializer(json_schema)
    return json_schema


class ConversionError(Exception):
    pass


class NoSuchConverter(ConversionError):
    pass


def convert_length_validator_factory(max_key, min_key):
    """
    :type max_key: str
    :type min_key: str
    """

    def validator_converter(schema_node, validator):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        converted = None
        if isinstance(validator, colander.Length):
            converted = OrderedDict()
            if validator.max is not None:
                converted[max_key] = validator.max
            if validator.min is not None:
                converted[min_key] = validator.min
        return converted

    return validator_converter


def convert_oneof_validator_factory(null_values=(None,)):
    """
    :type null_values: iter
    """

    def validator_converter(schema_node, validator):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        converted = None
        if isinstance(validator, colander.OneOf):
            converted = OrderedDict()
            converted['enum'] = list(validator.choices)
            if not schema_node.required:
                converted['enum'].extend(list(null_values))
        return converted

    return validator_converter


def convert_oneof_string_validator_factory():
    def validator_converter(schema_node, validator):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        converted = None
        if isinstance(validator, colander.OneOf):
            converted = OrderedDict()
            converted['enum'] = list(validator.choices)
        return converted

    return validator_converter


def convert_noneof_string_validator_factory():
    def validator_converter(schema_node, validator):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        converted = None
        if isinstance(validator, colander.NoneOf):
            converted = OrderedDict()
            converted['not'] = OrderedDict(enum=list(validator.forbidden))
        return converted

    return validator_converter


def convert_range_validator(schema_node, validator):
    """
    :type schema_node: colander.SchemaNode
    :type validator: colander.interfaces.Validator
    :rtype: dict
    """
    converted = None
    if isinstance(validator, colander.Range):
        converted = OrderedDict()
        if validator.max is not None:
            converted['maximum'] = validator.max
        if validator.min is not None:
            converted['minimum'] = validator.min
    return converted


def convert_regex_validator(schema_node, validator):
    """
    :type schema_node: colander.SchemaNode
    :type validator: colander.interfaces.Validator
    :rtype: dict
    """
    converted = None
    if isinstance(validator, colander.Regex):
        converted = OrderedDict()
        if hasattr(colander, 'url') and validator is colander.url:
            converted['format'] = 'uri'
        elif isinstance(validator, colander.Email):
            converted['format'] = 'email'
        else:
            converted['pattern'] = validator.match_object.pattern
    return converted


class ValidatorConversionDispatcher(object):
    def __init__(self, *converters):
        self.converters = converters

    def __call__(self, schema_node, validator=None):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        if validator is None:
            validator = schema_node.validator
        converted = OrderedDict()
        if validator is not None:
            for converter in (self.convert_all_validator,) + self.converters:
                ret = converter(schema_node, validator)
                if ret is not None:
                    converted = ret
                    break
        return converted

    def convert_all_validator(self, schema_node, validator):
        """
        :type schema_node: colander.SchemaNode
        :type validator: colander.interfaces.Validator
        :rtype: dict
        """
        converted = None
        if isinstance(validator, colander.All):
            converted = OrderedDict()
            for v in validator.validators:
                ret = self(schema_node, v)
                converted.update(ret)
        return converted


class TypeConverter(object):
    type = ''
    convert_validator = lambda self, schema_node: OrderedDict()

    def __init__(self, dispatcher):
        """
        :type dispatcher: TypeConversionDispatcher
        """
        self.dispatcher = dispatcher

    def convert_type(self, schema_node, converted):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        converted['type'] = self.type
        # if not schema_node.required:
        #     converted['type'] = [converted['type'], 'null']
        if schema_node.title:
            converted['title'] = schema_node.title
        if schema_node.description:
            converted['description'] = schema_node.description

        if (
            schema_node.missing is not colander.null
            and schema_node.missing is not colander.drop
            and schema_node.missing is not colander.required
        ):
            if callable(schema_node.missing):
                converted['default'] = schema_node.missing()
            else:
                converted['default'] = schema_node.missing

        if (
            schema_node.default is not colander.null
            and schema_node.default is not colander.drop
        ):
            if callable(schema_node.default):
                converted['default'] = schema_node.default()
            else:
                converted['default'] = schema_node.default
        return converted

    def __call__(self, schema_node, converted=None):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        if converted is None:
            converted = OrderedDict()
        converted = self.convert_type(schema_node, converted)
        converted.update(self.convert_validator(schema_node))
        return converted


class BaseStringTypeConverter(TypeConverter):
    type = 'string'
    format = None

    def convert_type(self, schema_node, converted):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        converted = super(BaseStringTypeConverter, self).convert_type(
            schema_node, converted
        )
        if schema_node.required:
            converted['minLength'] = 1
        if self.format is not None:
            converted['format'] = self.format
        return converted


class BooleanTypeConverter(TypeConverter):
    type = 'boolean'


class DateTypeConverter(BaseStringTypeConverter):
    format = 'date'


class DateTimeTypeConverter(BaseStringTypeConverter):
    format = 'date-time'


class NumberTypeConverter(TypeConverter):
    type = 'number'
    convert_validator = ValidatorConversionDispatcher(
        convert_range_validator,
        convert_oneof_validator_factory(),
    )


class IntegerTypeConverter(NumberTypeConverter):
    type = 'integer'


class StringTypeConverter(BaseStringTypeConverter):
    convert_validator = ValidatorConversionDispatcher(
        convert_length_validator_factory('maxLength', 'minLength'),
        convert_regex_validator,
        convert_oneof_string_validator_factory(),
        convert_noneof_string_validator_factory(),
    )


class DecimalTypeConverter(BaseStringTypeConverter):
    convert_validator = ValidatorConversionDispatcher(
        convert_range_validator,
        convert_oneof_validator_factory(),
    )


class TimeTypeConverter(BaseStringTypeConverter):
    format = 'time'


class ObjectTypeConverter(TypeConverter):
    type = 'object'

    def convert_type(self, schema_node, converted):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        converted = super(ObjectTypeConverter, self).convert_type(
            schema_node, converted
        )
        properties = OrderedDict()
        required = []
        for sub_node in schema_node.children:
            properties[sub_node.name] = self.dispatcher(sub_node)
            if sub_node.required:
                required.append(sub_node.name)
        converted['properties'] = properties
        if len(required) > 0:
            converted['required'] = required
        return converted


class ArrayTypeConverter(TypeConverter):
    type = 'array'
    convert_validator = ValidatorConversionDispatcher(
        convert_length_validator_factory('maxItems', 'minItems'),
    )

    def convert_type(self, schema_node, converted):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        converted = super(ArrayTypeConverter, self).convert_type(schema_node, converted)
        converted['items'] = self.dispatcher(schema_node.children[0])
        return converted


class NullableTypeConverter(TypeConverter):
    def __call__(self, schema_node, converted=None):
        """
        :type schema_node: colander.SchemaNode
        :type converted: dict
        :rtype: dict
        """
        if converted is None:
            converted = OrderedDict()
        orig_schema_type = schema_node.typ.typ
        schema_type = type(orig_schema_type)

        converter_class = self.dispatcher.converters.get(schema_type)
        if converter_class is None:
            raise NoSuchConverter(str(schema_type))
        converter = converter_class(self.dispatcher)
        converted = converter(schema_node, converted=converted)
        converted['type'] = [converted['type'], 'null']
        return converted


class TypeConversionDispatcher(object):
    converters = {
        schemas.Nullable: NullableTypeConverter,
        colander.Boolean: BooleanTypeConverter,
        colander.Date: DateTypeConverter,
        colander.DateTime: DateTimeTypeConverter,
        colander.Float: NumberTypeConverter,
        colander.Decimal: DecimalTypeConverter,
        colander.Money: DecimalTypeConverter,
        colander.Integer: IntegerTypeConverter,
        colander.Mapping: ObjectTypeConverter,
        schemas.UrlEncodeMapping: ObjectTypeConverter,
        colander.Sequence: ArrayTypeConverter,
        colander.Tuple: ArrayTypeConverter,
        colander.String: StringTypeConverter,
        schemas.EmptyString: StringTypeConverter,
        colander.Time: TimeTypeConverter,
        schemas.ResourceType: StringTypeConverter,
    }

    def __init__(self, converters=None):
        """
        :type converters: dict
        """
        if converters is not None:
            self.converters.update(converters)

    def __call__(self, schema_node):
        """
        :type schema_node: colander.SchemaNode
        :rtype: dict
        """
        schema_type = schema_node.typ
        schema_type = type(schema_type)
        converter_class = self.converters.get(schema_type)
        if converter_class is None:
            raise NoSuchConverter(str(schema_type))
        converter = converter_class(self)
        converted = converter(schema_node)
        return converted


def finalize_conversion(converted):
    """
    :type converted: dict
    :rtype: dict
    """
    converted['$schema'] = 'http://json-schema.org/draft-04/schema#'
    return converted


def convert(schema_node, converters=None):
    """
    :type schema_node: colander.SchemaNode
    :type converters: dict
    :rtype: dict
    """
    dispatcher = TypeConversionDispatcher(converters)
    converted = dispatcher(schema_node)
    converted = finalize_conversion(converted)
    return converted
