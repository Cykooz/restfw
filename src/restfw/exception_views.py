# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 03.08.2017
"""
from pyramid.httpexceptions import HTTPInternalServerError, HTTPForbidden, HTTPUnauthorized
from pyramid.interfaces import IExceptionResponse
from pyramid.security import forget
from pyramid.view import exception_view_config, forbidden_view_config

from .errors import http_exception_to_dict, ValidationError


@exception_view_config(context=IExceptionResponse, renderer='json')
def http_exception_view(exc_response, request):
    if exc_response.status_int == 304:
        # Not Modified
        return exc_response
    result = http_exception_to_dict(exc_response, request)
    request.response = exc_response
    return result


@forbidden_view_config()
def forbidden_view(exc_response, request):
    if exc_response.__class__ is HTTPForbidden:  # Exclude child classes
        if request.authenticated_userid is None:
            exc_response = HTTPUnauthorized()
            exc_response.headers.update(forget(request))
    return http_exception_view(exc_response, request)


@exception_view_config(context=ValidationError, renderer='json')
def invalid_parameters_view(exc_response, request):
    result = http_exception_to_dict(exc_response, request)
    request.response = exc_response
    return result


@exception_view_config(context=Exception, renderer='json', debug_or_testing=False)
def default_exception_view(exc, request):
    http_exc = HTTPInternalServerError(
        explanation=exc.__class__.__name__,
        detail=str(exc)
    )
    return http_exception_view(http_exc, request)
