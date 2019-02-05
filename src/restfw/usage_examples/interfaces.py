# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
from zope.interface import Interface, Attribute


class ISendTestingRequest(Interface):

    def __call__(params=None, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        """Send a testing request to resource"""


class IUsageExamples(Interface):
    entry_point_name = Attribute('Unique name of entry point described by this examples')
    resource = Attribute('Resource instance')
    resource_url = Attribute('The resource url')
    allowed_methods = Attribute('Allowed HTTP methods')
    request = Attribute("Pyramid's request instance")

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


class ISchemaInfoBuilder(Interface):

    def __call__(schema, request, context):
        """Build SchemaInfo instance for given schema.
        :type schema: Any
        :type request: pyramid.interfaces.IRequest
        :type context: Any
        :rtype: SchemaInfo
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
