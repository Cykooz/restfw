# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
import re
from contextlib import contextmanager
from typing import ContextManager, Dict, Optional, Union

import colander
from pyramid.config import Configurator
from pyramid.interfaces import IRequestFactory, IRootFactory
from pyramid.registry import Registry
from pyramid.request import Request, apply_request_extensions
from pyramid.threadlocal import RequestContext, get_current_request
from pyramid.traversal import DefaultRootFactory, find_resource
from webob.descriptors import serialize_etag_response
from zope.interface.interfaces import IInterface

from .errors import InvalidBodyFormat, ValidationError
from .events import Event
from .interfaces import IEvent, IHalResourceLinks, MethodOptions
from .typing import PyramidRequest


def is_testing(registry: Registry) -> bool:
    return registry.settings.get('testing', False) or registry.__name__ == 'testing'


is_testing_env = is_testing  # bw compatibility


def is_doc_building(registry: Registry) -> bool:
    return registry.settings.get('is_doc_building', False)


def is_debug(registry: Registry) -> bool:
    return registry.settings.get('debug', False)


def notify(event: Event, request: PyramidRequest):
    """Send event."""
    assert IEvent.providedBy(event), "Event object doesn't provide the IEvent"
    event.request = request
    request.registry.notify(event)


def scan_ignore(registry: Registry):
    result = [
        re.compile('tests$').search,
        re.compile('testing$').search,
        re.compile('conftest$').search,
        '.wsgi'
    ]
    if not is_doc_building(registry):
        result.append(re.compile('usage_examples$').search)
    return result


METHODS_WITH_BODY = {'POST', 'PUT', 'PATCH', 'DELETE'}


def get_input_data(context, request: PyramidRequest, schema: colander.SchemaNode) -> Union[dict, list]:
    if not schema:
        return {}

    content_type = request.content_type
    if request.method in METHODS_WITH_BODY and content_type.startswith('application/json'):
        try:
            data_dict = request.json_body
        except ValueError as e:
            raise InvalidBodyFormat(detail=str(e))
    else:
        data_dict = request.params

    try:
        schema = schema().bind(request=request, context=context)
        return schema.deserialize(data_dict)
    except colander.Invalid as e:
        raise colander_invalid_to_response(e)


def colander_invalid_to_response(exc: colander.Invalid):
    return ValidationError(exc.asdict())


def _create_error(
        node: colander.SchemaNode,
        message: str,
        child_node_path=None,
        value=None
) -> colander.Invalid:
    if child_node_path:
        pos = None
        child_node_name, _, child_node_path = child_node_path.partition('.')
        if isinstance(node.typ, colander.Positional):
            pos = int(child_node_name)
            child_node = node.children[0]
        else:
            child_node = node[child_node_name]
        error = colander.Invalid(node)
        error.add(_create_error(child_node, message, child_node_path, value), pos=pos)
    else:
        error = colander.Invalid(node, message, value)
    return error


def create_validation_error(schema_class, message, node_name=None, value=None):
    if schema_class is None:
        node_name = node_name or ''
        return ValidationError({node_name: message})
    error = _create_error(schema_class(), message, node_name, value)
    return colander_invalid_to_response(error)


def create_multi_validation_error(schema_class, errors: Dict[str, str]):
    if schema_class is None:
        return ValidationError(errors.copy())
    schema = schema_class()
    error = colander.Invalid(schema)
    for node_name, message in errors.items():
        error.add(
            _create_error(schema, message, node_name)
        )
    return colander_invalid_to_response(error)


def get_method_params(context, request: PyramidRequest) -> Union[dict, list]:
    request_method = request.method.lower()
    request_method = 'get' if request_method == 'head' else request_method

    method_options: Optional[MethodOptions] = getattr(
        context,
        'options_for_%s' % request_method,
        None
    )
    input_schema = method_options.input_schema if method_options else None
    return get_input_data(context, request, input_schema) if input_schema else {}


def get_paging_links(
        resource,
        request: PyramidRequest,
        offset: int,
        limit: int,
        has_next_page: bool,
) -> dict:
    links = {}
    query = request.GET.copy()
    query.pop('total_count', None)
    if has_next_page:
        query['offset'] = offset + limit
        links['next'] = {'href': request.resource_url(resource, query=query)}
    if offset > 0:
        prev_offset = max(0, offset - limit)
        query['offset'] = prev_offset
        links['prev'] = {'href': request.resource_url(resource, query=query)}
    return links


def register_resource_links_extender(config: Configurator, adapter, resource_class):
    """Add into the pyramid registry an adapter for extend resource links.
    :param config: A pyramid configurator.
    :param adapter: Some callable object (takes only resource instance) which implements IResourceLinks.
    :param resource_class: Class or interface of resource which links will be extended by adapter.
    """
    config.registry.registerAdapter(adapter, required=resource_class, provided=IHalResourceLinks)


def find_resource_by_type(resource, path, class_or_interface):
    context = find_resource(resource, path)
    if IInterface.providedBy(class_or_interface):
        test = class_or_interface.providedBy
    else:
        test = lambda arg: isinstance(arg, class_or_interface)
    if not test(context):
        raise KeyError('%r type is not %s' % (context, class_or_interface))
    return context


def force_utf8(v):
    if isinstance(v, str):
        return v.encode('utf-8')
    return v


def force_dict_utf8(d):
    values = []
    for k, v in d.items():
        values.append((force_utf8(k), force_utf8(v)))
    return dict(values)


def get_pyramid_root(request=None):
    request = request or get_current_request()
    if getattr(request, 'root', None) is None:
        root_factory = request.registry.queryUtility(IRootFactory, default=DefaultRootFactory)
        root = root_factory(request)  # Initialise pyramid root
        request.root = root
    return request.root


@contextmanager
def open_pyramid_request(registry: Registry, path='http://localhost') -> ContextManager[PyramidRequest]:
    request_factory = registry.queryUtility(IRequestFactory, default=Request)
    request: PyramidRequest = request_factory.blank(path)
    request.registry = registry
    apply_request_extensions(request)
    get_pyramid_root(request)
    context = RequestContext(request)
    context.begin()
    try:
        yield request
    finally:
        request._process_finished_callbacks()
        context.end()


def get_object_fullname(o):
    module = o.__module__
    if module is None or module == str.__class__.__module__:
        return o.__name__  # Avoid reporting __builtin__
    return '%s.%s' % (module, o.__name__)


class ETag:
    __slots__ = ('value', 'is_strict')

    def __init__(self, value: str, is_strict=True):
        self.value = value
        self.is_strict = is_strict

    def __repr__(self):
        return '<ETag %s>' % self.serialize()

    def serialize(self) -> str:
        return serialize_etag_response((self.value, self.is_strict))
