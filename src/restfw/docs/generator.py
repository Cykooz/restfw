# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.04.2015
"""
import json
from typing import Iterable

from pyramid.encode import urlencode

from .utils import header, get_resource_url, method_description
from .schemadoc import get_schema_description


def get_resource_doc(web_app, resource_info):
    # type: (object, mountbit.restfw.testing.resource_info.ResourceInfo) -> Iterable[str]

    resource = resource_info.resource

    # List of urls
    for line in header('Resource path', '='):
        yield line
    yield get_resource_url(resource)
    yield ''

    allowed_methods = resource.get_allowed_methods()

    for method in ['get', 'put', 'patch', 'post', 'delete']:
        if method.upper() not in allowed_methods:
            continue

        method_func = getattr(resource, 'http_%s' % method, None)
        method_options = getattr(resource, 'options_for_%s' % method, None)
        if not method_func or not method_options:
            continue

        for line in header(method.upper(), '='):
            yield line
        for line in method_description(method_func):
            yield line

        # Method schemas
        if method_options.input_schema or method_options.output_schema:
            for line in header('Data schemas', '-'):
                yield line

            if method_options.input_schema:
                for line in get_schema_description(method_options.input_schema,
                                                   resource_info.registry, is_input=True):
                    yield line

            if method_options.output_schema:
                for line in get_schema_description(method_options.output_schema,
                                                   resource_info.registry, is_input=False):
                    yield line
        yield ''

        for line in get_examples(web_app, resource_info, method):
            yield line


def get_examples(web_app, resource_info, method):
    #: :type: list of mountbit.restfw.resource_info.ParamsResult
    requests = getattr(resource_info, '%s_requests' % method, None)
    if requests is None:
        return

    resource_url = resource_info.resource_url
    need_title = True
    for params in requests:
        if not params.is_success_status:
            continue

        if need_title:
            for line in header('Examples', '-'):
                yield line
            need_title = False

        url = resource_url
        if method in ('get', 'head') and params.params:
            url += '?' + urlencode(params.params, doseq=True)

        yield 'Request:'
        yield ''
        yield '  **{}** \\{}'.format(method.upper(), url)
        yield ''

        if params.headers:
            yield '  Headers::'
            yield ''
            for name, value in params.headers.items():
                yield '    {}: {}'.format(name, value)
            yield ''

        if params.params and method not in ('get', 'head'):
            yield '  Body:'
            yield ''
            yield '  .. code-block:: js'
            yield ''
            for line in json.dumps(params.params, indent=2).split('\n'):
                yield '    {}'.format(line)
            yield ''

        web_method_name = method if method in ('get', 'head') else '%s_json' % method
        web_method = getattr(web_app, web_method_name, None)
        response = web_method(
            resource_url, params=params.params, headers=params.headers,
            exception=params.exception, status=params.status
        )
        yield 'Response:'
        yield ''
        yield '  Status: %s' % response.status
        yield ''
        if 'Location' in response.headers:
            yield '  Headers::'
            yield ''
            yield '    Location: {}'.format(response.headers['Location'])
            yield ''

        if response.status_int != 204:
            yield '  Body:'
            yield ''
            yield '  .. code-block:: js'
            yield ''
            for line in json.dumps(response.json_body, indent=2).split('\n'):
                yield '    {}'.format(line)
            yield ''

        yield ''
        yield '----'
        yield ''

    #
    # resource = resource_info.resource
    # request = get_current_request()
    # input_data = doc_prepare.get_example_request(self.method, resource)
    # if input_data is None:
    #     return
    #
    # for line in utils.header('Example', '-'):
    #     yield line
    #
    # request.input_data = input_data
    # request.GET.clear()
    # if self.method == 'GET':
    #     for key, value in input_data.items():
    #         request.GET[key] = unicode(value)
    # result = self.original_view(resource, request)
    # result = JSON_RENDER(result, {'request': request})
    # result = json.loads(result)
    #
    # if self.method == 'GET':
    #     url = self.resource_info.get_url(**input_data)
    # else:
    #     url = self.resource_info.get_url()
    # request.GET.clear()
    #
    # yield 'Request:'
    # yield ''
    # yield '  **{}** \\{}'.format(self.method, url)
    # yield ''
    # if input_data and self.method != 'GET':
    #     yield '  Body:'
    #     yield ''
    #     yield '  .. code-block:: js'
    #     yield ''
    #     for line in json.dumps(input_data, indent=2).split('\n'):
    #         yield '    {}'.format(line)
    #     yield ''
    #
    # yield 'Response body:'
    # yield ''
    # yield '  .. code-block:: js'
    # yield ''
    # for line in json.dumps(result, indent=2).split('\n'):
    #     yield '    {}'.format(line)
    # yield ''
