# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from typing import Any, Set, Tuple

from pyramid.interfaces import ILocation
from zope.interface import Attribute, Interface

from .typing import PyramidRequest


class MethodOptions:
    __slots__ = ('input_schema', 'output_schema', 'permission')

    def __init__(self, input_schema, output_schema, permission=None):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.permission = permission

    def replace(self, **kwargs) -> 'MethodOptions':
        """Create copy of current instance and replace some fields in it."""
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in self.__slots__
        }
        for key in self.__slots__:
            if key not in kwargs:
                kwargs[key] = getattr(self, key, None)
        return self.__class__(**kwargs)


class IResource(ILocation):
    """Interface for resource"""

    # __resource_name__ = Attribute('Name of resource')
    # url_placeholder = Attribute('Placeholder for resource URL in documentation.')

    def __getitem__(key):
        """Returns a sub-resource or raises exception KeyError.
        :param key: name of sub-resource
        :type key: str
        :rtype: IResource
        :raise: KeyError
        """

    def get_registry():
        """Returns registry instance.
        :rtype: pyramid.registry.Registry
        """

    def get_etag():
        """Returns value of ETag header for the resource or None.
        :rtype: restfw.utils.ETag or None
        """

    def http_post(request: PyramidRequest, params: dict) -> Tuple['IResource', bool]:
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        """

    def http_put(request: PyramidRequest, params: dict) -> bool:
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        """

    def http_patch(request: PyramidRequest, params: dict) -> bool:
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        """

    def http_delete(request: PyramidRequest, params: dict):
        """Delete the resource. Returns None or some resource."""


class IResourceView(Interface):
    """Interface for minimal resource view."""

    request = Attribute('Current request instance')
    resource = Attribute('Instance of resource')
    options_for_get = Attribute('Options for GET HTTP method.')
    options_for_post = Attribute('Options for POST HTTP method.')
    options_for_put = Attribute('Options for PUT HTTP method.')
    options_for_patch = Attribute('Options for PATCH HTTP method.')
    options_for_delete = Attribute('Options for DELETE HTTP method.')

    def __json__():
        """Returns a representation of resource as object
        suitable for JSON encoding."""

    def get_allowed_methods() -> Set[str]:
        """Returns a set of allowed HTTP methods for the resource view."""

    def http_options() -> Any:
        """Returns response for OPTIONS method of HTTP."""

    def http_head() -> Any:
        """This method may be used in derived classes to overwrite
        a default implementation for HEAD request handler.
        """

    def http_get() -> Any:
        """Returns representation of the resource as any object that
        can be processed by default render or as raw response."""

    def http_post() -> Any:
        """Returns a new or modified resource and a flag indicating that the
        resource was created or not.
        """

    def http_put() -> Any:
        """Returns a new or modified resource and a flag indicating that the
        resource was created or not.
        """

    def http_patch() -> Any:
        """Returns a new or modified resource and a flag indicating that the
        resource was created or not.
        """

    def http_delete() -> Any:
        """Delete the resource. Returns None or some resource."""


class IRoot(IResource):
    """Interface for root resource."""
    registry = Attribute('Registry of Pyramid application')
    request = Attribute('Current request object (deprecated)')


class ISubResourceFabric(Interface):

    def __call__(parent):
        """Returns instance of sub-resource of parent resource.
        :type parent: IResource
        :rtype: IResource or None
        """


# HAL (https://tools.ietf.org/html/draft-kelly-json-hal-08)

class IHalResource(IResource):
    """Interface of HAL-resources."""


class IHalResourceView(IResourceView):
    """Interface for view that MAY contains embedded resources."""

    def get_links() -> dict:
        """Returns dict with links (content of '_links' field from HAL) for resource."""

    def as_embedded() -> dict:
        """Returns resource representation when it is used as an embedded resource."""


class IHalResourceWithEmbeddedView(IResourceView):
    """Interface for view that MAY contains embedded resources."""

    def get_embedded(params: dict):
        """Returns EmbeddedResources instance.
        :rtype: EmbeddedResources
        """


class IHalResourceLinks(Interface):
    """Interface of adapter for extend resource links."""

    def get_links(request):
        """Returns dict with links (content of "_links" field from HAL) for resource.
        :type request: pyramid.request.Request
        :rtype: dict
        """


class IExternalLinkAdapter(Interface):
    title = Attribute('Title for schema node')
    description = Attribute('Description for schema node')
    optional = Attribute('Link is optional')
    templated = Attribute('Link is templated')

    def get_link(request):
        """
        :type request: pyramid.request.Request
        :rtype: str or None
        """


class IExternalLinkFabric(Interface):

    def __call__(request, resource):
        """
        :type request: pyramid.request.Request
        :type resource: IHalResource
        :rtype: str or None
        """


# Events

class IEvent(Interface):
    request = Attribute('Current request')


class IRootCreated(IEvent):
    """An event type that is emitted after root object was created."""
    root = Attribute('The root object')
