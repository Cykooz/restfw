# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
from webtest import TestResponse
from zope.interface import Attribute, Interface


class ISendTestingRequest(Interface):

    def __call__(params=None, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False) -> TestResponse:
        """Send a testing request to resource"""


class IUsageExamples(Interface):
    entry_point_name = Attribute('Unique name of entry point described by this examples')
    resource = Attribute('Resource instance')
    resource_url = Attribute('The resource url')
    view = Attribute('Instance of ResourceView class.')
    allowed_methods = Attribute('Allowed HTTP methods')
    request = Attribute("Pyramid's request instance")
    default_auth = Attribute('Authorization string used by default for all requests')

    def authorize_request(params, headers, auth=None):
        """Add authorization information into request with given params and headers.
        :type params: dict or None
        :type headers: dict or None
        :param auth: Some string used for authorization. For example '<login>:<password>'.
        :type auth: str or None
        :return: Tuple with a new version of params and headers.
        """

    def send(
            params=None, headers=None, auth=None, result=None, result_headers=None,
            exception=None, status=None, description=None, exclude_from_doc=False
    ) -> TestResponse:
        """Send a testing request to resource"""

    def get_requests():
        """Calls function 'send' with parameters of GET requests."""

    def put_requests():
        """Calls function 'send' with parameters of PUT requests."""

    def patch_requests():
        """Calls function 'send' with parameters of PATCH requests."""

    def post_requests():
        """Calls function 'send' with parameters of POST requests."""

    def delete_requests():
        """Calls function 'send' with parameters of DELETE requests."""


class IUsageExamplesFabric(Interface):

    def __call__(request):
        """Create instance of IUsageExamples.
        :type request: pyramid.request.Request
        :rtype: IUsageExamples
        """


class IPrepareEnv(Interface):
    """Object used to prepare environment before create IUsageExamples instance and run it.

    For example, this object may be used to clean up databases and prepare request instance.
    """

    def __call__(request):
        """
        :type request: pyramid.interfaces.IRequest
        """


class ISchemaSerializer(Interface):

    def __call__(schema, request, context):
        """Returns serialized version of given schema.
        :type schema: Any
        :type request: pyramid.interfaces.IRequest
        :type context: Any
        :rtype: Any
        """


class IPrincipalFormatter(Interface):

    def __call__(principal, request, context):
        """Convert principal name into human readable test.
        :type principal: Any
        :type request: pyramid.interfaces.IRequest
        :type context: Any
        :rtype: str
        """


class IDocStringExtractor(Interface):

    def __call__(code_object):
        """Extract and prepare docstring to using in documentation.
        :param code_object: object of code (function, method or class)
        :type code_object: Any
        :rtype: list[unicode]
        """


class IDocStringLineFilter(Interface):

    def __call__(line):
        """Returns True if given line must be excluded from docstring.
        :type line: str
        :rtype: bool
        """
