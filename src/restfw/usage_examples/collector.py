# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
from __future__ import unicode_literals

import logging
from collections import OrderedDict
from copy import deepcopy

import six
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.location import lineage
from pyramid.security import Authenticated, Everyone
from six.moves import http_client
from typing import List, Dict

from . import interfaces, structs
from .colander2jsonschema import colander_2_json_schema
from .utils import default_docstring_extractor, sphinx_doc_filter
from ..testing import resource_testing
from ..utils import get_object_fullname, open_pyramid_request


class UsageExamplesCollector(object):
    """Collector uses to collect full information about all registered
    resource usage examples.
    """
    ALL_POSSIBLE_METHODS = ('GET', 'PUT', 'PATCH', 'POST', 'DELETE')

    def __init__(self, web_app, prepare_env=None, schema_serializer=None,
                 principal_formatter=None,
                 docstring_extractor=default_docstring_extractor,
                 docstring_filter=sphinx_doc_filter,
                 logger=None):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type prepare_env: interfaces.IPrepareEnv or None
        :type schema_serializer: interfaces.ISchemaSerializer or None
        :type principal_formatter: interfaces.IPrincipalFormatter or None
        :type docstring_extractor: interfaces.IDocStringExtractor
        :type docstring_filter: interfaces.IDocStringLineFilter or None
        :param logger: logger instance
        """
        self.web_app = web_app
        self.registry = web_app.registry
        self._prepare_env = prepare_env
        self._schema_serializer = schema_serializer or colander_2_json_schema
        self._principal_formatter = principal_formatter
        self._docstring_extractor = docstring_extractor
        self._docstring_filter = docstring_filter
        self._logger = logger or logging

        self.resources_info = {}  # type: Dict[str, structs.ResourceInfo]
        self.entry_points_info = {}  # type: Dict[str, structs.EntryPointInfo]
        self.url_to_ep_id = {}  # type: Dict[str, str]

    def collect(self):
        resources_info = {}
        entry_points_info = {}
        url_to_ep_id = {}

        for ep_id, fabric in self.registry.getUtilitiesFor(interfaces.IUsageExamplesFabric):
            with open_pyramid_request(self.registry) as request:
                if self._prepare_env:
                    self._prepare_env(request)
                usage_examples = fabric(request)  # type: interfaces.IUsageExamples
                if usage_examples is None:
                    # Examples do not support current environment
                    continue

                self._logger.info('Collecting information form "%s".', ep_id)

                resource = usage_examples.resource
                resource_class_name = get_object_fullname(resource.__class__)

                if resource_class_name not in resources_info:
                    resources_info[resource_class_name] = structs.ResourceInfo(
                        class_name=resource_class_name,
                        description=self._get_code_object_doc(resource.__class__)
                    )
                resources_info[resource_class_name].count_of_entry_points += 1

                path_elements = self._get_resource_path_elements(resource)
                methods = self._get_methods_info(usage_examples)

                entry_points_info[ep_id] = structs.EntryPointInfo(
                    usage_examples.entry_point_name,
                    examples_class_name=get_object_fullname(usage_examples.__class__),
                    resource_class_name=resource_class_name,
                    url_elements=path_elements,
                    methods=methods,
                    description=self._get_code_object_doc(usage_examples.__class__)
                )
                url = '/'.join(e.value for e in path_elements)
                if url in url_to_ep_id and url_to_ep_id[url] != ep_id:
                    self._logger.warning(
                        'URL "%s" of entry point "%s" already used by entry point "%s"',
                        url, ep_id, url_to_ep_id[url]
                    )
                url_to_ep_id[url] = ep_id

        # Fill property 'ep_id' in url elements
        for entry_point_info in six.itervalues(entry_points_info):
            url = ''
            for element in entry_point_info.url_elements:
                if url:
                    url += '/'
                url += element.value
                element.ep_id = url_to_ep_id.get(url, None)

        self.resources_info = resources_info
        self.entry_points_info = entry_points_info
        self.url_to_ep_id = url_to_ep_id

    def _get_code_object_doc(self, code_object):
        """
        :rtype: list[unicode]
        """
        lines = self._docstring_extractor(code_object)
        if self._docstring_filter:
            lines = [line for line in lines if not self._docstring_filter(line)]
        if lines:
            # Remove last empty line
            lines = lines[:-1]
        return lines

    @staticmethod
    def _get_resource_path_elements(resource, skip_root=True):
        """
        :rtype: list[structs.UrlElement]
        """
        elements = []
        for resource in lineage(resource):
            value = getattr(resource, 'url_placeholder', None)
            if not value:
                value = resource.__name__ or ''
            class_name = get_object_fullname(resource.__class__)
            element = structs.UrlElement(value, class_name, None)
            elements.append(element)
        elements.reverse()
        if skip_root and elements:
            elements = elements[1:]
        return elements

    def _get_methods_info(self, usage_examples):
        """
        :type usage_examples: interfaces.IUsageExamples
        :rtype: dict[str, structs.MethodInfo]
        """
        request = usage_examples.request
        resource = usage_examples.resource
        allowed_methods = resource.get_allowed_methods()
        available_methods = [m.lower() for m in self.ALL_POSSIBLE_METHODS if m in allowed_methods]

        result = OrderedDict()

        for method in available_methods:
            method_func = getattr(resource, 'http_%s' % method, None)
            method_options = getattr(resource, 'options_for_%s' % method, None)
            if not method_func or not method_options:
                continue

            authorization_policy = self.registry.queryUtility(IAuthorizationPolicy)
            method_permission = method_options.permission or method
            allowed_principals = authorization_policy.principals_allowed_by_permission(
                resource, method_permission
            )
            if Everyone in allowed_principals:
                allowed_principals = {Everyone}
            elif Authenticated in allowed_principals:
                allowed_principals = {Authenticated}
            if self._principal_formatter is not None:
                allowed_principals = {
                    self._principal_formatter(p, request, resource)
                    for p in allowed_principals
                }

            result[method.upper()] = structs.MethodInfo(
                examples_info=self._get_examples_info(usage_examples, method),
                input_schema=self._get_schema_info(method_options.input_schema, request, resource),
                output_schema=self._get_schema_info(method_options.output_schema, request, resource),
                allowed_principals=allowed_principals,
                description=self._get_code_object_doc(method_func),
            )
        return result

    def _get_examples_info(self, usage_examples, method):
        """Execute all examples of method and return list of ExampleInfo.

        :type usage_examples: interfaces.IUsageExamples
        :param method:
        :rtype: list[structs.ExampleInfo]
        """
        send_requests = getattr(usage_examples, '%s_requests' % method, None)
        if send_requests is None:
            return []

        resource_url = usage_examples.resource_url
        send = _ExampleInfoCollector(self.web_app, resource_url, method)
        send_requests(send)

        return send.results

    def _get_schema_info(self, schema_class, request, context):
        """Build SchemaInfo instance for given schema class.
        :type schema_class: colander.SchemaNode
        :type request: pyramid.interfaces.IRequest
        :type context: restfw.interfaces.IResource
        :rtype: SchemaInfo or None
        """
        serialized_schema = self._schema_serializer(schema_class, request, context)
        if not serialized_schema:
            return
        return structs.SchemaInfo(
            class_name=get_object_fullname(schema_class),
            serialized_schema=serialized_schema,
            description=self._get_code_object_doc(schema_class),
        )


class _ExampleInfoCollector(resource_testing.RequestsTester):

    def __init__(self, web_app, resource_url, method):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type resource_url: str
        :type method: str
        """
        super(_ExampleInfoCollector, self).__init__(web_app, resource_url)
        self.method = method
        self.results = []  # type: List[structs.ExampleInfo]

    def __call__(self, params=resource_testing.DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None, description=None):
        params = params if params is not resource_testing.DEFAULT else {}
        web_method_name = self.method if self.method in ('get', 'head') else '%s_json' % self.method
        web_method = getattr(self.web_app, web_method_name, None)
        response = web_method(
            self.resource_url, params=params, headers=headers,
            exception=exception, status=status
        )

        request_info = structs.RequestInfo(
            url=self.resource_url,
            headers=deepcopy(headers),
            params=deepcopy(params),
        )

        status_code = response.status_code
        status_name = http_client.responses.get(status_code, '')
        json_body = response.json_body if response.status_code != 204 else None
        if status_code >= 400 and json_body:
            status_name = json_body.get('code', status_name)

        response_info = structs.ResponseInfo(
            status_code, status_name,
            headers=deepcopy(dict(response.headers)),
            expected_headers=deepcopy(dict(result_headers)) if result_headers else None,
            json_body=response.json_body if response.status_code != 204 else None
        )
        self.results.append(structs.ExampleInfo(request_info, response_info, description))
