# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.01.2019
"""
from zope.interface import implementer, provider

from .errors import ValidationError
from .interfaces import IUsageExamples, IUsageExamplesFabric, ISendTestingRequest


@provider(IUsageExamplesFabric)
@implementer(IUsageExamples)
class UsageExamples(object):

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

    @property
    def entry_point_name(self):
        """
        :rtype: str
        """
        name = self.__class__.__name__
        suffix = 'Examples'
        if name.endswith(suffix):
            name = name[:-len(suffix)]
        return name

    def prepare_resource(self):
        """
        :rtype: restfw.interfaces.IResource
        """
        raise NotImplementedError

    def get_requests(self, send):
        """
        :type send: ISendTestingRequest
        """
        pass

    def put_requests(self, send):
        """
        :type send: ISendTestingRequest
        """
        pass

    def patch_requests(self, send):
        """
        :type send: ISendTestingRequest
        """
        pass

    def post_requests(self, send):
        """
        :type send: ISendTestingRequest
        """
        pass

    def delete_requests(self, send):
        """
        :type send: ISendTestingRequest
        """
        pass
