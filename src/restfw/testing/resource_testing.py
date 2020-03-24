# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from copy import deepcopy

from pyramid.httpexceptions import HTTPException
from webtest.forms import Upload
from zope.interface import implementer

from ..interfaces import IHalResourceWithEmbedded
from ..schemas import LISTING_CONF
from ..usage_examples import UsageExamples
from ..usage_examples.interfaces import ISendTestingRequest


DEFAULT = object()


class RequestsTester(object):

    def __init__(self, web_app, resource_examples):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type resource_examples: UsageExamples
        """
        self.web_app = web_app
        self.resource_examples = resource_examples
        self.resource_url = resource_examples.resource_url
        self.calls_count = 0

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        raise NotImplementedError


@implementer(ISendTestingRequest)
class GetRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.resource_examples.authorize_request(params, headers, auth)

        head_res = self.web_app.head(self.resource_url, params=params, headers=headers,
                                     exception=exception, status=status)
        assert head_res.body == b''

        get_res = self.web_app.get(self.resource_url, params=params, headers=headers,
                                   exception=exception, status=status)
        if result is not None:
            if get_res.content_type == 'application/json':
                assert get_res.json_body == result
            else:
                assert get_res.text == result
        if result_headers is not None:
            assert dict(get_res.headers) == result_headers

        if get_res.headers is not None:
            assert dict(head_res.headers) == dict(get_res.headers)


@implementer(ISendTestingRequest)
class PutRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.resource_examples.authorize_request(params, headers, auth)

        put_method = self.web_app.put_json
        if isinstance(params, dict) and any(isinstance(v, Upload) for v in params.values()):
            put_method = self.web_app.put
        res = put_method(self.resource_url, params=params, headers=headers,
                         exception=exception, status=status)
        if status == 201 and 'Location' in res.headers:
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        if result_headers is not None:
            assert dict(res.headers) == result_headers


@implementer(ISendTestingRequest)
class PatchRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.resource_examples.authorize_request(params, headers, auth)

        patch_method = self.web_app.patch_json
        if isinstance(params, dict) and any(isinstance(v, Upload) for v in params.values()):
            patch_method = self.web_app.patch
        res = patch_method(self.resource_url, params=params, headers=headers,
                           exception=exception, status=status)
        if status == 201 and 'Location' in res.headers:
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        if result_headers is not None:
            assert dict(res.headers) == result_headers


@implementer(ISendTestingRequest)
class PostRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.resource_examples.authorize_request(params, headers, auth)

        post_method = self.web_app.post_json
        if isinstance(params, dict) and any(isinstance(v, Upload) for v in params.values()):
            post_method = self.web_app.post
        res = post_method(self.resource_url, params=params, headers=headers,
                          exception=exception, status=status)
        if status == 201 and 'Location' in res.headers:
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        if result_headers is not None:
            assert dict(res.headers) == result_headers


@implementer(ISendTestingRequest)
class DeleteRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, auth=None, result=None, result_headers=None,
                 exception=None, status=None, description=None, exclude_from_doc=False):
        """
        :type params: dict or list or str or None
        :type headers: dict or None
        :type auth: str or None
        :type result: dict or None
        :type result_headers: dict or None
        :type exception: HTTPException
        :type status: int
        :type description: str or None
        :type exclude_from_doc: bool
        """
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.resource_examples.authorize_request(params, headers, auth)

        res = self.web_app.delete_json(self.resource_url, params=params, headers=headers,
                                       exception=exception, status=status)
        if status == 204:
            assert res.body == b''
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        if result_headers is not None:
            assert dict(res.headers) == result_headers


def assert_resource(resource_examples, web_app):
    """
    :type resource_examples: UsageExamples
    :type web_app: restfw.testing.webapp.WebApp
    """
    info_name = resource_examples.__class__.__name__

    # Test GET requests
    send = GetRequestsTester(web_app, resource_examples)
    if resource_examples.get_requests:
        resource_examples.get_requests(send)
    if 'GET' in resource_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any GET requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends GET requests to resource'.format(info_name)

    # Test listing of embedded resources
    if (IHalResourceWithEmbedded.providedBy(resource_examples.resource) and
            resource_examples.test_listing):
        orig_listing_conf = deepcopy(LISTING_CONF)
        try:
            assert_container_listing(resource_examples, web_app)
        finally:
            LISTING_CONF.clear()
            LISTING_CONF.update(orig_listing_conf)

    # Test PUT requests
    send = PutRequestsTester(web_app, resource_examples)
    if resource_examples.put_requests:
        resource_examples.put_requests(send)
    if 'PUT' in resource_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any PUT requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends PUT requests to resource'.format(info_name)

    # Test PATCH requests
    send = PatchRequestsTester(web_app, resource_examples)
    if resource_examples.patch_requests:
        resource_examples.patch_requests(send)
    if 'PATCH' in resource_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any PATCH requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends PATCH requests to resource'.format(info_name)

    # Test POST requests
    send = PostRequestsTester(web_app, resource_examples)
    if resource_examples.post_requests:
        resource_examples.post_requests(send)
    if 'POST' in resource_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any POST requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends POST requests to resource'.format(info_name)

    # Test DELETE requests
    send = DeleteRequestsTester(web_app, resource_examples)
    if resource_examples.delete_requests:
        resource_examples.delete_requests(send)
    if 'DELETE' in resource_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any DELETE requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends DELETE requests to resource'.format(info_name)


def assert_container_listing(resource_examples, web_app):
    """
    :type resource_examples: UsageExamples
    :type web_app: restfw.testing.webapp.WebApp
    """
    LISTING_CONF['max_limit'] = 2
    resource_url = resource_examples.resource_url
    base_headers = resource_examples.headers_for_listing  # Deprecated

    params = {'limit': 1, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.head(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' in res.headers
    total_count = int(res.headers['X-Total-Count'])
    assert total_count >= 3

    params, headers = resource_examples.authorize_request(None, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    params = {'total_count': False}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers

    params = {'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    next_link = res['_links']['next']['href']
    params, headers = resource_examples.authorize_request(None, base_headers)
    res = web_app.get(next_link, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == min(total_count - 2, 2)

    prev_link = res['_links']['prev']['href']
    res = web_app.get(prev_link, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    # `limit` is less than `max_value_of_limit`
    params = {'limit': 1, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 1

    # `limit` is greater than `max_value_of_limit`
    params = {'limit': 10, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 2

    params = {'offset': 2, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == min(total_count - 2, 2)

    params = {'limit': 1, 'offset': 1, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 1

    params = {'embedded': False}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    params = {'embedded': False, 'total_count': True}
    params, headers = resource_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    ValidationError = resource_examples.ValidationError

    params = {'offset': 'off', 'limit': 'lim'}
    params, headers = resource_examples.authorize_request(params, base_headers)
    web_app.get(resource_url, params=params, headers=headers,
                exception=ValidationError({'limit': '"lim" is not a number',
                                           'offset': '"off" is not a number'}))

    params = {'offset': -1, 'limit': -1}
    params, headers = resource_examples.authorize_request(params, base_headers)
    web_app.get(resource_url, params=params, headers=headers,
                exception=ValidationError({'limit': '-1 is less than minimum value 0',
                                           'offset': '-1 is less than minimum value 0'}))
