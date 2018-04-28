# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 03.08.2017
"""
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.interfaces import IExceptionResponse
from pyramid.view import exception_view_config

from .errors import http_exception_to_dict, ValidationError


@exception_view_config(context=IExceptionResponse, renderer='json')
def http_exception_view(exc_response, request):
    result = http_exception_to_dict(exc_response, request)
    request.response = exc_response
    return result


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
