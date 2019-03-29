# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from __future__ import unicode_literals

import six
from pyramid import httpexceptions
from pyramid.traversal import resource_path


def exception__str__(self):
    return six.text_type(self.detail or self.explanation)


httpexceptions.HTTPException.__str__ = exception__str__


def http_exception_to_dict(exc, request, include_status=False):
    """
    :type exc: httpexceptions.HTTPException
    :type request: pyramid.request.Request
    :type include_status: bool
    :rtype: dict
    """
    status_code = exc.status_code
    exc_class_name = exc.__class__.__name__
    if exc_class_name.startswith('HTTP'):
        if status_code == 200:
            return {}
        exc_class_name = exc_class_name[4:]
    detail = exc.detail or {}
    if not isinstance(detail, dict):
        detail = {'msg': detail}

    result = {
        'code': exc_class_name,
        'description': exc.explanation or exc.title,
        'detail': detail
    }
    if include_status:
        result['status'] = status_code
    if status_code == 404 and 'resource' not in detail:
        resource = getattr(request, 'context', None)
        if resource:
            elements = [request.view_name] if request.view_name else []
            detail['resource'] = resource_path(resource, *elements)
            if detail.get('msg') == request.path_info:
                # Delete default message with full path from request
                del detail['msg']
    return result


class InvalidBodyFormat(httpexceptions.HTTPBadRequest):
    explanation = 'The request body has wrong format. Body must be valid JSON string.'


class ValidationError(httpexceptions.HTTPUnprocessableEntity):
    explanation = 'The request has wrong parameters.'


class ResultValidationError(httpexceptions.HTTPInternalServerError):
    title = 'Result Validation Error'
    explanation = 'The result has wrong parameters.'
