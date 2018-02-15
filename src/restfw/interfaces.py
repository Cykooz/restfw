# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from __future__ import unicode_literals

from pyramid.interfaces import ILocation
from zope.interface import Interface, Attribute


class MethodOptions(object):

    __slots__ = ('input_schema', 'output_schema', 'permission')

    def __init__(self, input_schema, output_schema, permission=None):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.permission = permission


class IResource(ILocation):
    """Interface for resource"""

    # __resource_name__ = Attribute('Name of resource')
    # url_placeholder = Attribute('Placeholder for resource URL in documentation.')
    options_for_get = Attribute('Options for GET HTTP method.')
    options_for_post = Attribute('Options for POST HTTP method.')
    options_for_put = Attribute('Options for PUT HTTP method.')
    options_for_patch = Attribute('Options for PATCH HTTP method.')
    options_for_delete = Attribute('Options for DELETE HTTP method.')

    def as_dict(request):
        """Returns a dict that represents the resource.
        :type request: pyramid.request.Request
        :rtype: dict
        """

    def get_allowed_methods():
        # type: () -> set
        """Returns a set of allowed HTTP methods for the resource."""

    def http_head(request, params):
        """This method may be used in derived classes to overwrite
        a default implementation for HEAD request handler.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: IResource
        """

    def http_get(request, params):
        """Returns representation of the resource.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: IResource
        """

    def http_post(request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: (IResource, bool)
        """

    def http_put(request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: (IResource, bool)
        """

    def http_patch(request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: (IResource, bool)
        """

    def http_delete(request, params):
        """Delete the resource. Returns None or some resource
        :type request: pyramid.request.Request
        :type params: dict
        """

    def get_request():
        """Returns current request instance.
        :rtype: pyramid.registry.Registry
        """


class IContainer(IResource):
    """Interface for resource that can returns child resource by it name"""

    def __getitem__(key):
        """Returns object from container.
        :param key: name of object in the container.
        """


# HAL (https://tools.ietf.org/html/draft-kelly-json-hal-08)


class IHalResource(IResource):

    def get_links(request):
        """Returns dict with links (content of '_links' field from HAL) for resource.
        :type request: pyramid.request.Request
        :rtype: dict
        """

    def as_embedded(request):
        """Returns resource representation when it is used as an embedded resource.
        :type request: pyramid.request.Request
        :rtype: dict
        """


class IHalResourceLinks(Interface):
    """Interface of adapter for extend resource links."""

    def get_links(request):
        """Returns dict with links (content of "_links" field from HAL) for resource.
        :type request: pyramid.request.Request
        :rtype: dict
        """


class IHalResourceWithEmbedded(IResource):
    """Interface for resource that MAY contains embedded resources."""

    def get_embedded(request, params):
        """Returns EmbeddedResult instance.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: EmbeddedResult
        """


class IHalContainerWithEmbedded(IHalResourceWithEmbedded, IContainer):
    pass


class IRoot(IContainer):
    """Interface for root container"""

    request = Attribute('Current request object')


# Events

class IEvent(Interface):
    request = Attribute('Current request')


class IRootCreated(IEvent):
    """An event type that is emitted after root object was created."""
    root = Attribute('The root object')


# Docs

class ISendTestingRequest(Interface):

    def __call__(params=None, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        """Send a testing request to resource"""


class IResourceInfo(Interface):

    resource = Attribute('Resource instance')
    resource_url = Attribute('The resource url')
    allowed_methods = Attribute('Allowed HTTP methods')

    def get_requests(send):
        """Calls function 'send' with parameters of GET requests.
        :type send: ISendTestingRequest
        """

    def put_requests(send):
        """Calls function 'send' with parameters of PUT requests.
        :type send: ISendTestingRequest
        """

    def patch_requests(send):
        """Calls function 'send' with parameters of PATCH requests.
        :type send: ISendTestingRequest
        """

    def post_requests(send):
        """Calls function 'send' with parameters of POST requests.
        :type send: ISendTestingRequest
        """

    def delete_requests(send):
        """Calls function 'send' with parameters of DELETE requests.
        :type send: ISendTestingRequest
        """


class IResourceInfoFabric(Interface):

    def __call__(self, registry, root):
        """Returns instance of IResourceInfo."""
