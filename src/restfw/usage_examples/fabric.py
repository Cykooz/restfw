# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.01.2019
"""
import abc
from contextlib import contextmanager
from typing import Dict, Optional, Union

from webtest import TestResponse
from zope.interface import implementer, provider

from .interfaces import ISendTestingRequest, IUsageExamples, IUsageExamplesFabric
from .utils import basic_auth_value
from ..errors import ValidationError
from ..interfaces import IResource
from ..typing import PyramidRequest
from ..views import get_resource_view


DEFAULT = object()
Params = Union[dict, list, str, bytes]


@provider(IUsageExamplesFabric)
@implementer(IUsageExamples)
class UsageExamples(abc.ABC):
    ValidationError = ValidationError
    headers_for_listing = None  # Deprecated
    default_auth = ''
    test_listing = True

    def __init__(self, request: PyramidRequest):
        self.registry = request.registry
        self.root = request.root
        self.request = request
        self.resource = self.prepare_resource()
        self.resource_url = self.request.resource_url(self.resource)
        self.view = get_resource_view(self.resource, request)
        self.allowed_methods = self.view.get_allowed_methods()
        self._send: Optional[ISendTestingRequest] = None

    @property
    def entry_point_name(self) -> str:
        name = self.__class__.__name__
        suffix = 'Examples'
        if name.endswith(suffix):
            name = name[:-len(suffix)]
        return name

    def authorize_request(self, params: Optional[Params], headers: Optional[dict], auth: Optional[str] = None):
        """Add authorization information into request with given params and headers.
        :param auth: Some string used for authorization. For example '<login>:<password>'.
        :return: Tuple with a new version of params and headers.
        """
        if auth is None:
            auth = self.default_auth
        if auth:
            headers = headers.copy() if headers else {}
            user_name, _, password = auth.partition(':')
            headers['Authorization'] = basic_auth_value(user_name, password)
        return params, headers

    @abc.abstractmethod
    def prepare_resource(self) -> IResource:
        ...

    @contextmanager
    def send_function(self, send: ISendTestingRequest):
        old_send = self._send
        try:
            self._send = send
            yield
        finally:
            self._send = old_send

    def send(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result=None,
            result_headers: Optional[dict] = None,
            exception=None,
            status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False
    ) -> TestResponse:
        assert self._send is not None
        return self._send(
            params=params, headers=headers, auth=auth,
            result=result, result_headers=result_headers,
            exception=exception, status=status,
            description=description,
            exclude_from_doc=exclude_from_doc,
        )

    def get_requests(self):
        pass

    def put_requests(self):
        pass

    def patch_requests(self):
        pass

    def post_requests(self):
        pass

    def delete_requests(self):
        pass
