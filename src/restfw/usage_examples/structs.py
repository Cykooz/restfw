# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2019

Data structures to store information about resources, entry points
and usage examples collected by `UsageExamplesCollector`.
"""


class UrlElement(object):

    def __init__(self, value, resource_class_name, ep_id=None):
        """
        :type value: str
        :type resource_class_name: str
        :type ep_id: str or None
        """
        self.value = value
        self.resource_class_name = resource_class_name
        self.ep_id = ep_id


class ResourceInfo(object):

    def __init__(self, class_name, description=None):
        """
        :type class_name: str
        :type description: list[unicode]
        """
        self.class_name = class_name
        self.description = description or []
        self.count_of_entry_points = 0


class SchemaInfo(object):

    def __init__(self, class_name, serialized_schema):
        """
        :type class_name: str
        :type serialized_schema: Any
        """
        self.class_name = class_name
        self.serialized_schema = serialized_schema


class RequestInfo(object):

    def __init__(self, url, headers=None, params=None):
        """
        :type url: str
        :type headers: dict or None
        :type params: dict or None
        """
        self.url = url
        self.headers = headers
        self.params = params


class ResponseInfo(object):

    def __init__(self, status_code, status_name, headers=None, json_body=None):
        """
        :type status_code: int
        :type status_name: str
        :type headers: dict or None
        :type json_body: dict or list or str or None
        """
        self.status_code = status_code
        self.status_name = status_name
        self.headers = headers
        self.json_body = json_body


class ExampleInfo(object):

    def __init__(self, request_info, response_info):
        """
        :type request_info: RequestInfo
        :type response_info: ResponseInfo
        """
        self.request_info = request_info
        self.response_info = response_info


class Examples(object):

    def __init__(self, examples_info):
        """
        :type examples_info: list of ExampleInfo
        """
        self.examples_info = examples_info
        self.all_statuses = sorted(set(e.response_info.status_code for e in examples_info))


class MethodInfo(object):

    def __init__(self, examples_info, input_schema=None, output_schema=None,
                 allowed_principals=None, description=None):
        """
        :type examples_info: list of ExampleInfo
        :type input_schema: SchemaInfo or None
        :type output_schema: SchemaInfo or None
        :type allowed_principals: list[str]
        :type description: list[unicode]
        """
        self.examples_info = examples_info
        self.description = description or []
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.allowed_principals = allowed_principals or []


class EntryPointInfo(object):

    def __init__(self, name, resource_class_name, url_elements, methods, description=None):
        """
        :type name: str
        :type resource_class_name: str
        :type url_elements: list[UrlElement]
        :type methods: dict[str, MethodInfo]
        :type description: list[unicode]
        """
        self.name = name
        self.resource_class_name = resource_class_name
        self.url_elements = url_elements
        self.methods = methods
        self.description = description or []
