# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from zope.interface import implementer, provider

from .errors import ValidationError
from .interfaces import IResourceInfo, IResourceInfoFabric, ISendTestingRequest


@provider(IResourceInfoFabric)
@implementer(IResourceInfo)
class ResourceInfo(object):

    ValidationError = ValidationError
    headers_for_listing = None
    test_listing = True

    def __init__(self, request):
        """
        :type request: pyramid.request.Request
        """
        self.registry = request.registry
        self.root = request.root
        self.request = request
        self.resource = self.prepare_resource()
        self.request.context = self.resource
        self.resource_url = self.request.resource_url(self.resource)
        self.allowed_methods = self.resource.get_allowed_methods()

    def prepare_resource(self):
        return None

    def get_requests(self, send):
        # type: (ISendTestingRequest) -> None
        pass

    def put_requests(self, send):
        # type: (ISendTestingRequest) -> None
        pass

    def patch_requests(self, send):
        # type: (ISendTestingRequest) -> None
        pass

    def post_requests(self, send):
        # type: (ISendTestingRequest) -> None
        pass

    def delete_requests(self, send):
        # type: (ISendTestingRequest) -> None
        pass
