# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
import re
from contextlib import contextmanager
from typing import ContextManager

import colander
from pyramid.interfaces import IRequestFactory, IRootFactory
from pyramid.request import Request, apply_request_extensions
from pyramid.threadlocal import RequestContext, get_current_request
from pyramid.traversal import DefaultRootFactory, find_resource
from webob.descriptors import serialize_etag_response
from zope.interface.interfaces import IInterface

from .errors import InvalidBodyFormat, ValidationError
from .interfaces import IEvent, IHalResourceLinks
from .renderers import json_renderer


JSON_RENDER = json_renderer(None)


def is_testing(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: bool
    """
    return registry.settings.get('testing', False) or registry.__name__ == 'testing'


is_testing_env = is_testing  # bw compatibility


def is_doc_building(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: bool
    """
    return registry.settings.get('is_doc_building', False)


def is_debug(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: bool
    """
    return registry.settings.get('debug', False)


def notify(event, request):
    """Send event.
    :param event: restfw.events.Event
    :param request: pyramid.request.Request
    """
    assert IEvent.providedBy(event), "Event object doesn't provide the IEvent"
    event.request = request
    request.registry.notify(event)


def scan_ignore(registry):
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


def get_input_data(context, request, schema):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :type schema: colander.SchemaNode
    :rtype: dict or list
    """
    if not schema:
        return {}

    content_type = request.content_type
    if request.method in METHODS_WITH_BODY and content_type.startswith('application/json'):
        try:
            data_dict = request.json_body
        except ValueError as e:
            raise InvalidBodyFormat(detail=e.message)
    else:
        data_dict = request.params

    try:
        schema = schema().bind(request=request, context=context)
        return schema.deserialize(data_dict)
    except colander.Invalid as e:
        raise colander_invalid_to_response(e)


def colander_invalid_to_response(exc):
    """
    :type exc: colander.Invalid
    :rtype: pyramid.response.Response
    """
    return ValidationError(exc.asdict())


def _create_error(node, message, child_node_path=None, value=None):
    """
    :type node: colander.SchemaNode
    :type message: str
    :type child_node_path: str
    :type value: Any
    :rtype: colander.Invalid
    """
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
    error = _create_error(schema_class(), message, node_name, value)
    return colander_invalid_to_response(error)


def get_method_params(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: Union[dict, list]
    """
    request_method = request.method.lower()
    request_method = 'get' if request_method == 'head' else request_method

    #: :type: MethodOptions
    method_options = getattr(context, 'options_for_%s' % request_method, None)
    input_schema = method_options.input_schema if method_options else None
    return get_input_data(context, request, input_schema) if input_schema else {}


def get_paging_links(resource, request, offset, limit, has_next_page):
    """
    :type resource: IResource
    :type request: pyramid.request.Request
    :type offset: int
    :type limit: int
    :type has_next_page: bool
    :rtype: dict
    """
    links = {}
    query = request.GET.copy()
    if has_next_page:
        query['offset'] = offset + limit
        links['next'] = {'href': request.resource_url(resource, query=query)}
    if offset > 0:
        prev_offset = max(0, offset - limit)
        query['offset'] = prev_offset
        links['prev'] = {'href': request.resource_url(resource, query=query)}
    return links


def register_resource_links_extender(config, adapter, resource_class):
    """Add into the pyramid registry an adapter for extend resource links.
    :param config: A pyramid configurator.
    :type config: pyramid.config.Configurator
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
def open_pyramid_request(registry, path='http://localhost'):
    """
    :type registry: pyramid.registry.Registry
    :type path: str
    :rtype: ContextManager[pyramid.request.Request]
    """
    request_factory = registry.queryUtility(IRequestFactory, default=Request)
    request = request_factory.blank(path)
    request.registry = registry
    apply_request_extensions(request)
    get_pyramid_root(request)
    context = RequestContext(request)
    context.begin()
    try:
        yield request
    finally:
        context.end()


def get_object_fullname(o):
    module = o.__module__
    if module is None or module == str.__class__.__module__:
        return o.__name__  # Avoid reporting __builtin__
    return '%s.%s' % (module, o.__name__)


class ETag(object):
    __slots__ = ('value', 'is_strict')

    def __init__(self, value, is_strict=True):
        """
        :type value: str
        :type is_strict: bool
        """
        self.value = value
        self.is_strict = is_strict

    def __repr__(self):
        return '<ETag %s>' % self.serialize()

    def serialize(self):
        """
        :rtype: str
        """
        return serialize_etag_response((self.value, self.is_strict))
