# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from zope.interface import implementer, provider

from .interfaces import IResourceInfo, IResourceInfoFabric


DEFAULT = object()


class ParamsResult(object):

    def __init__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (dict, dict, dict, dict, pyramid.httpexceptions.HTTPException, int) -> None
        self.params = params if params is not DEFAULT else {}
        self.headers = headers
        self.result = result
        self.result_headers = result_headers
        self.exception = exception
        self.status = status

    @property
    def is_success_status(self):
        status = self.exception.code if self.exception else self.status
        return status is None or 200 <= status < 300


@provider(IResourceInfoFabric)
@implementer(IResourceInfo)
class ResourceInfo(object):

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

    @property
    def get_requests(self):
        # type: () -> Iterable[ParamsResult]
        return None

    @property
    def put_requests(self):
        # type: () -> Iterable[ParamsResult]
        return None

    @property
    def patch_requests(self):
        # type: () -> Iterable[ParamsResult]
        return None

    @property
    def post_requests(self):
        # type: () -> Iterable[ParamsResult]
        return None

    @property
    def delete_requests(self):
        # type: () -> Iterable[ParamsResult]
        return None
