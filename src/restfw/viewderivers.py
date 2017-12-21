# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
import json
from typing import Callable

import colander
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.viewderivers import INGRESS, VIEW

from .errors import ResultValidationError
from .interfaces import IResource
from .utils import is_testing_env


def check_request_method_view(view, info):
    """
    :type view: Callable[[object, object], object]
    :type info: pyramid.interfaces.IViewDeriverInfo
    :rtype: object
    """

    def mapped_view(context, request):
        # type: (IResource, pyramid.request.Request) -> object
        method = request.method
        if (context is not request.root and
                IResource.providedBy(context) and
                method != 'OPTIONS'):
            if method == 'HEAD':
                method = 'GET'
            if method not in context.get_allowed_methods():
                raise HTTPMethodNotAllowed('The method %s is not allowed for this resource.' % request.method)
        return view(context, request)

    return mapped_view


def check_result_schema(view, info):
    # type: (Callable[[object, object], pyramid.response.Response], pyramid.interfaces.IViewDeriverInfo) -> object

    def mapped_view(context, request):
        # type: (object, pyramid.request.Request) -> object
        response = view(context, request)
        if (context is not request.root and
                IResource.providedBy(context) and
                request.method not in {'HEAD', 'OPTIONS'}):
            method = request.method.lower()
            method_options = getattr(context, 'options_for_%s' % method, None)
            output_schema = method_options.output_schema if method_options else None
            if output_schema:
                try:
                    rendered = response.body
                    schema = output_schema().bind(request=request, context=context)
                    cstruct = json.loads(rendered)
                    appstruct = schema.deserialize(cstruct)
                    result_keys = set(cstruct.keys())
                    schema_keys = set(appstruct.keys())
                    diff = result_keys.symmetric_difference(schema_keys)
                    if diff:
                        detail = {k: 'Not expected field' for k in diff}
                        raise ResultValidationError(detail)
                except colander.Invalid as e:
                    raise ResultValidationError(e.asdict())
        return response

    return mapped_view


def register_view_derivers(config):
    config.add_view_deriver(check_request_method_view,
                            name='check_request_method_view',
                            under=INGRESS)
    if is_testing_env(config.registry):
        config.add_view_deriver(check_result_schema,
                                name='check_result_schema')
