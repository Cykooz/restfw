# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from pyramid.router import Router


try:
    import pytest
    pytest.register_assert_rewrite(
        'restfw.testing.resource_testing',
        'restfw.testing.webapp',
    )
except (ImportError, AttributeError):
    pass

from contextlib import contextmanager
from pyramid.interfaces import IRequestFactory, IRootFactory
from pyramid.request import Request, apply_request_extensions
from pyramid.threadlocal import get_current_request, RequestContext
from pyramid.traversal import DefaultRootFactory

from .resource_testing import assert_resource


def get_pyramid_root(request=None):
    request = request or get_current_request()
    if getattr(request, 'root', None) is None:
        root_factory = request.registry.queryUtility(IRootFactory, default=DefaultRootFactory)
        root = root_factory(request)  # Initialise pyramid root
        request.root = root
    return request.root


@contextmanager
def open_pyramid_request(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: pyramid.request.Request
    """
    request_factory = registry.queryUtility(IRequestFactory, default=Request)
    request = request_factory.blank('http://localhost')
    request.registry = registry
    apply_request_extensions(request)
    get_pyramid_root(request)
    context = RequestContext(request)
    context.begin()
    try:
        yield request
    finally:
        context.end()
