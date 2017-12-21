# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 19.08.2016
"""
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.traversal import find_root
from zope.interface import implementer

from . import schemas, interfaces


@implementer(interfaces.IResource)
class Resource(object):
    __parent__ = None
    __name__ = None

    def __str__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.__name__)

    def __repr__(self):
        return str(self)

    def as_dict(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        return {}

    def __json__(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        return self.as_dict(request)

    @property
    def __resource_name__(self):
        return self.__class__.__name__

    def get_allowed_methods(self):
        # type: () -> set
        methods = {'OPTIONS'}
        for method in ('get', 'put', 'patch', 'delete', 'post'):
            method_options = 'options_for_%s' % method
            method_options = getattr(self, method_options, None)
            if method_options is not None:
                methods.add(method.upper())
        if 'GET' in methods:
            methods.add('HEAD')
        return methods

    def get_request(self):
        """
        :rtype: pyramid.registry.Registry
        """
        root = find_root(self)
        if root is not self and root.request:
            return root.request

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.ResourceSchema)

    def http_get(self, request, params):
        return self

    options_for_post = None

    def http_post(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'POST'})

    options_for_put = None

    def http_put(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PUT'})

    options_for_patch = None

    def http_patch(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PATCH'})

    options_for_delete = None

    def http_delete(self, request, params):
        """Delete the resource."""
        raise HTTPMethodNotAllowed(detail={'method': 'DELETE'})
