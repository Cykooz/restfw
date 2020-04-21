# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 19.08.2016
"""
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.registry import Registry
from pyramid.traversal import find_root
from typing import Generator, Tuple
from zope.interface import implementer

from . import interfaces, schemas


@implementer(interfaces.IResource)
class Resource(object):
    __parent__ = None
    __name__ = None

    def __str__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.__name__)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        if not key:
            raise KeyError(key)
        resource = None
        registry = self.get_registry()
        key = str(key)
        if registry:
            try:
                resource = registry.queryAdapter(self, interfaces.IResource, name=key)
            except KeyError:
                pass
        if not resource:
            raise KeyError(key)
        resource.__name__ = key
        resource.__parent__ = self
        return resource

    def get_sub_resources(self, registry):
        """
        :type registry: Registry
        :rtype: Generator[Tuple[str, interfaces.IResource]]
        """
        for name, sub_resource in registry.getAdapters((self,), interfaces.IResource):
            yield name, sub_resource

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
        """
        :rtype: set[str]
        """
        methods = {'OPTIONS'}
        for method in ('get', 'put', 'patch', 'delete', 'post'):
            method_options = 'options_for_%s' % method
            method_options = getattr(self, method_options, None)
            if method_options is not None:
                methods.add(method.upper())
        if 'GET' in methods:
            methods.add('HEAD')
        return methods

    def get_registry(self):
        """
        :rtype: pyramid.registry.Registry
        """
        root = find_root(self)
        return root.registry

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.ResourceSchema)

    def http_head(self, request, params):
        """This method may be used in derived classes to overwrite
        a default implementation for HEAD request handler.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: IResource
        """
        return self.http_get(request, params)

    def http_get(self, request, params):
        """Returns a resource, any of it representation or any response instance."""
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
