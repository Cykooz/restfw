# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
import re

import colander
# from mountbit.backend.docs.utils import is_doc_building
import six
from pyramid.traversal import find_resource
from zope.interface.interfaces import IInterface

from .errors import ValidationError, InvalidBodyFormat
from .interfaces import IEvent, IHalResourceLinks, IResourceInfoFabric
from .renderers import json_renderer


JSON_RENDER = json_renderer(None)


def is_testing_env(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: bool
    """
    return registry.settings.get('testing', False) or registry.__name__ == 'testing'


def is_doc_building(registry):
    return registry.settings.get('is_doc_building', False)


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
        re.compile('resources_info$').search,
        '.wsgi'
    ]
    if not is_doc_building(registry):
        result.append('.docs')
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
        if request.method == 'DELETE':
            # https://github.com/Pylons/webob/issues/351
            post_request = request.copy()
            post_request.method = 'POST'
        else:
            post_request = request
        data_dict = post_request.params

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


def create_validation_error(schema_class, message, node_name=None, value=None):
    schema = schema_class()
    node = schema[node_name] if node_name else schema
    error = colander.Invalid(node, message, value)
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
    # type: (pyramid.config.Configurator, object, object) -> None
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


def register_resource_info(config, info_class, name):
    config.registry.registerUtility(info_class, provided=IResourceInfoFabric, name=name)


def force_utf8(v):
    if isinstance(v, six.text_type):
        return v.encode('utf-8')
    return v


def force_dict_utf8(d):
    values = []
    for k, v in six.iteritems(d):
        values.append((force_utf8(k), force_utf8(v)))
    return dict(values)
