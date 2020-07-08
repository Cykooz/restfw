# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from pyramid import httpexceptions
from pyramid.interfaces import ILocation
from pyramid.view import view_config

from .interfaces import IResource
from .utils import get_method_params


def call_resource_method(resource, request):
    """
    :type resource: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    params = get_method_params(resource, request)
    request_method = request.method.lower()
    method = 'http_%s' % request_method
    method = getattr(resource, method)
    # We do not need to check the method, because it was do
    # in the check_request_method_view view deriver.
    return method(request, params)


@view_config(request_method='OPTIONS', context=IResource)
def resource_options(context, request):
    allowed_methods = context.get_allowed_methods()
    allowed_methods = ', '.join(allowed_methods)
    request.response.headers['Allow'] = allowed_methods

    if 'Access-Control-Request-Method' in request.headers:
        request.response.headers['Access-Control-Allow-Methods'] = allowed_methods

    return request.response


@view_config(request_method=['HEAD', 'GET'], context=IResource, permission='get')
def resource_get(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    result = call_resource_method(context, request)
    _try_add_etag(request, result, context)
    return result


@view_config(request_method='POST', context=IResource, permission='post')
def resource_post(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    result, created = call_resource_method(context, request)
    if result is None:
        return httpexceptions.HTTPNoContent()
    if created:
        request.response.status = 201
        if ILocation.providedBy(result):
            request.response.headers['Location'] = request.resource_url(result)
    _try_add_etag(request, result)
    return result


@view_config(request_method='PUT', context=IResource, permission='put')
def resource_put(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    result, created = call_resource_method(context, request)
    if result is None:
        return httpexceptions.HTTPNoContent()
    if created:
        request.response.status = 201
        if ILocation.providedBy(result):
            request.response.headers['Location'] = request.resource_url(result)
    _try_add_etag(request, result, context)
    return result


@view_config(request_method='PATCH', context=IResource, permission='patch')
def resource_patch(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    result, created = call_resource_method(context, request)
    if result is None:
        return httpexceptions.HTTPNoContent()
    if created:
        request.response.status = 201
        if ILocation.providedBy(result):
            request.response.headers['Location'] = request.resource_url(result)
    _try_add_etag(request, result, context)
    return result


@view_config(request_method='DELETE', context=IResource, permission='delete')
def resource_delete(context, request):
    """
    :type context: IResource
    :type request: pyramid.request.Request
    :rtype: object
    """
    result = call_resource_method(context, request)
    if result is None:
        return httpexceptions.HTTPNoContent()
    _try_add_etag(request, result)
    return result


def _try_add_etag(request, result, context=None):
    etag = None
    if IResource.providedBy(result):
        etag = result.get_etag()
    elif context is not None:
        etag = context.get_etag()
    if etag is not None:
        request.response.etag = (etag.value, etag.is_strict)
