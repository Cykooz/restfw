# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.01.2019
"""
from zope.interface import implementer, provider

from .interfaces import ISendTestingRequest, IUsageExamples, IUsageExamplesFabric
from .utils import basic_auth_value
from ..errors import ValidationError
from ..typing import PyramidRequest
from ..views import get_resource_view


@provider(IUsageExamplesFabric)
@implementer(IUsageExamples)
class UsageExamples(object):

    ValidationError = ValidationError
    headers_for_listing = None  # Deprecated
    default_auth = ''
    test_listing = True

    def __init__(self, request: PyramidRequest):
        self.registry = request.registry
        self.root = request.root
        self.request = request
        self.resource = self.prepare_resource()
        self.request.context = self.resource
        self.resource_url = self.request.resource_url(self.resource)
        self.view = get_resource_view(self.resource, request)
        self.allowed_methods = self.view.get_allowed_methods()

    @property
    def entry_point_name(self) -> str:
        name = self.__class__.__name__
        suffix = 'Examples'
        if name.endswith(suffix):
            name = name[:-len(suffix)]
        return name

    def authorize_request(self, params, headers, auth=None):
        """Add authorization information into request with given params and headers.
        :type params: dict or None
        :type headers: dict or None
        :param auth: Some string used for authorization. For example '<login>:<password>'.
        :type auth: str or None
        :return: Tuple with a new version of params and headers.
        """
        if auth is None:
            auth = self.default_auth
        if auth:
            headers = headers.copy() if headers else {}
            user_name, _, password = auth.partition(':')
            headers['Authorization'] = basic_auth_value(user_name, password)
        return params, headers

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
