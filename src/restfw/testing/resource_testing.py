# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from copy import deepcopy
from typing import Dict, Optional

from pyramid.httpexceptions import HTTPNotModified, HTTPPreconditionFailed
from webtest import TestResponse
from webtest.forms import Upload
from zope.interface import implementer

from .webapp import WebApp
from ..interfaces import IHalResourceWithEmbeddedView
from ..schemas import LISTING_CONF
from ..usage_examples import UsageExamples
from ..usage_examples.fabric import DEFAULT, Params
from ..usage_examples.interfaces import ISendTestingRequest


class RequestsTester:

    def __init__(self, web_app: WebApp, usage_examples: UsageExamples):
        self.web_app = web_app
        self.usage_examples = usage_examples
        self.resource_url = usage_examples.resource_url
        self.calls_count = 0

    def __call__(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result: Optional[dict] = None,
            result_headers: Optional[Dict[str, str]] = None,
            exception=None, status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False,
    ) -> TestResponse:
        raise NotImplementedError


@implementer(ISendTestingRequest)
class GetRequestsTester(RequestsTester):
    was_if_match = False
    was_if_none_match = False

    def __call__(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result: Optional[dict] = None,
            result_headers: Optional[Dict[str, str]] = None,
            exception=None, status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False,
    ) -> TestResponse:
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.usage_examples.authorize_request(params, headers, auth)

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

        if get_res.status_code in (200, 201, 204):
            etag = self.usage_examples.resource.get_etag()
            if etag and (not result_headers or 'ETag' not in result_headers):
                assert 'ETag' in get_res.headers, (
                    "Resource has ETag, but headers of the response don't contain ETag."
                )
                assert get_res.headers['ETag'] == etag.serialize()

        if headers:
            if 'If-Match' in headers:
                self.was_if_match = True
            if 'If-None-Match' in headers:
                self.was_if_none_match = True

        return get_res


@implementer(ISendTestingRequest)
class PutPatchRequestsTester(RequestsTester):
    was_if_match = False
    was_if_none_match = False

    def __init__(self, web_app: WebApp, usage_examples: UsageExamples, method_name: str):
        super(PutPatchRequestsTester, self).__init__(web_app, usage_examples)
        self._json_method = getattr(self.web_app, '%s_json' % method_name)
        self._method = getattr(self.web_app, method_name)

    def __call__(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result: Optional[dict] = None,
            result_headers: Optional[Dict[str, str]] = None,
            exception=None, status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False,
    ) -> TestResponse:
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.usage_examples.authorize_request(params, headers, auth)

        method_func = self._json_method
        if isinstance(params, dict) and any(isinstance(v, Upload) for v in params.values()):
            method_func = self._method
        res = method_func(
            self.resource_url, params=params, headers=headers,
            exception=exception, status=status,
        )
        if status == 201 and 'Location' in res.headers:
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        if result_headers is not None:
            assert dict(res.headers) == result_headers

        if res.status_code in (200, 201):
            etag = self.usage_examples.resource.get_etag()
            if etag and (not result_headers or 'ETag' not in result_headers):
                assert 'ETag' in res.headers, (
                    "Resource has ETag, but headers of the response don't contain ETag."
                )
                resource = self.usage_examples.resource
                parent = resource.__parent__
                if parent and 'GET' in self.usage_examples.allowed_methods:
                    # Get a new resource instance with refreshed internal state
                    etag = parent[resource.__name__].get_etag().serialize()
                else:
                    # WARNING: This value of etag may be obsolete
                    etag = etag.serialize()
                assert res.headers['ETag'] == etag

        if headers:
            if 'If-Match' in headers:
                self.was_if_match = True
            if 'If-None-Match' in headers:
                self.was_if_none_match = True

        return res


@implementer(ISendTestingRequest)
class PostRequestsTester(RequestsTester):

    def __call__(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result: Optional[dict] = None,
            result_headers: Optional[Dict[str, str]] = None,
            exception=None, status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False,
    ) -> TestResponse:
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.usage_examples.authorize_request(params, headers, auth)

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

        return res


@implementer(ISendTestingRequest)
class DeleteRequestsTester(RequestsTester):

    def __call__(
            self,
            params: Optional[Params] = DEFAULT,
            headers: Optional[Dict[str, str]] = None,
            auth: Optional[str] = None,
            result: Optional[dict] = None,
            result_headers: Optional[Dict[str, str]] = None,
            exception=None, status: Optional[int] = None,
            description: Optional[str] = None,
            exclude_from_doc=False,
    ) -> TestResponse:
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        params, headers = self.usage_examples.authorize_request(params, headers, auth)

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

        return res


def assert_resource(usage_examples: UsageExamples, web_app: WebApp):
    _assert_get_and_head(usage_examples, web_app)
    _assert_put_and_patch(usage_examples, web_app)
    _assert_post(usage_examples, web_app)
    _assert_delete(usage_examples, web_app)


def _assert_get_and_head(usage_examples: UsageExamples, web_app: WebApp):
    """Test GET requests."""
    info_name = usage_examples.__class__.__name__
    send = GetRequestsTester(web_app, usage_examples)
    if usage_examples.get_requests:
        with usage_examples.send_function(send):
            usage_examples.get_requests()
    if 'GET' not in usage_examples.allowed_methods:
        assert send.calls_count == 0, '{} sends GET requests to resource'.format(info_name)
        return

    assert send.calls_count > 0, '{} has not any GET requests'.format(info_name)

    etag = usage_examples.resource.get_etag()
    if etag:
        etag = etag.serialize()
        if not send.was_if_match:
            send(
                headers={'If-Match': '"__bad_etag__"'},
                exception=HTTPPreconditionFailed({'etag': etag}),
            )
        if not send.was_if_none_match:
            send(
                headers={'If-None-Match': etag},
                exception=HTTPNotModified,
            )

    # Test listing of embedded resources
    if (IHalResourceWithEmbeddedView.providedBy(usage_examples.view) and
            usage_examples.test_listing):
        orig_listing_conf = deepcopy(LISTING_CONF)
        try:
            assert_container_listing(usage_examples, web_app)
        finally:
            LISTING_CONF.clear()
            LISTING_CONF.update(orig_listing_conf)


def _assert_put_and_patch(usage_examples: UsageExamples, web_app: WebApp):
    """Test PUT and PATH requests."""
    info_name = usage_examples.__class__.__name__
    test_params = [
        ('PUT', usage_examples.put_requests),
        ('PATCH', usage_examples.patch_requests),
    ]
    for http_method, examples_method in test_params:
        send = PutPatchRequestsTester(web_app, usage_examples, http_method.lower())
        if examples_method:
            with usage_examples.send_function(send):
                examples_method()
        if http_method not in usage_examples.allowed_methods:
            assert send.calls_count == 0, '{} sends {} requests to resource'.format(info_name, http_method)
            continue

        assert send.calls_count > 0, '{} has not any {} requests'.format(info_name, http_method)

        etag = usage_examples.resource.get_etag()
        if etag:
            # if 'HEAD' in resource_examples.allowed_methods:
            #     params, headers = resource_examples.authorize_request(None, None, None)
            #     head_res = web_app.head(resource_examples.resource_url, params=params, headers=headers)
            #     etag = head_res.headers['ETag']
            resource = usage_examples.resource
            parent = resource.__parent__
            if parent and 'GET' in usage_examples.allowed_methods:
                # Get a new resource instance with refreshed internal state
                etag = parent[resource.__name__].get_etag().serialize()
            else:
                # WARNING: This value of etag may be obsolete
                etag = etag.serialize()

            if not send.was_if_match:
                send(
                    headers={'If-Match': '"__bad_etag__"'},
                    exception=HTTPPreconditionFailed({'etag': etag}),
                )
            if not send.was_if_none_match:
                send(
                    headers={'If-None-Match': etag},
                    exception=HTTPPreconditionFailed({'etag': etag}),
                )


def _assert_post(usage_examples: UsageExamples, web_app: WebApp):
    """Test POST requests."""
    info_name = usage_examples.__class__.__name__
    send = PostRequestsTester(web_app, usage_examples)
    if usage_examples.post_requests:
        with usage_examples.send_function(send):
            usage_examples.post_requests()
    if 'POST' in usage_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any POST requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends POST requests to resource'.format(info_name)


def _assert_delete(usage_examples: UsageExamples, web_app: WebApp):
    """Test DELETE requests."""
    info_name = usage_examples.__class__.__name__
    send = DeleteRequestsTester(web_app, usage_examples)
    if usage_examples.delete_requests:
        with usage_examples.send_function(send):
            usage_examples.delete_requests()
    if 'DELETE' in usage_examples.allowed_methods:
        assert send.calls_count > 0, '{} has not any DELETE requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends DELETE requests to resource'.format(info_name)


def assert_container_listing(usage_examples: UsageExamples, web_app: WebApp):
    LISTING_CONF['max_limit'] = 2
    resource_url = usage_examples.resource_url
    base_headers = usage_examples.headers_for_listing  # Deprecated

    params = {'limit': 1, 'total_count': True}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.head(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' in res.headers
    total_count = int(res.headers['X-Total-Count'])
    assert total_count >= 3

    params, headers = usage_examples.authorize_request(None, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    params = {'total_count': False}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers

    params = {'total_count': True}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    next_link = res['_links']['next']['href']
    assert 'total_count=' not in next_link
    params, headers = usage_examples.authorize_request(None, base_headers)
    res = web_app.get(next_link, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == min(total_count - 2, 2)

    is_offset_paging = 'offset=' in next_link

    prev_link = res['_links'].get('prev', {}).get('href', '')
    if is_offset_paging:
        # Offset based pagination must have a link to previews page
        assert prev_link > ''

    if prev_link:
        assert 'total_count=' not in prev_link
        res = web_app.get(prev_link, headers=headers)
        assert 'X-Total-Count' not in res.headers
        res = res.json_body
        embedded = list(res['_embedded'].values())[0]
        assert len(embedded) == 2

    # `limit` is less than `max_value_of_limit`
    params = {'limit': 1, 'total_count': True}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 1

    # `limit` is greater than `max_value_of_limit`
    params = {'limit': 10, 'total_count': True}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert res.headers['X-Total-Count'] == str(total_count)
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 2

    if is_offset_paging:
        params = {'offset': 2, 'total_count': True}
        params, headers = usage_examples.authorize_request(params, base_headers)
        res = web_app.get(resource_url, params=params, headers=headers)
        assert res.headers['X-Total-Count'] == str(total_count)
        embedded = list(res.json_body['_embedded'].values())[0]
        assert len(embedded) == min(total_count - 2, 2)

        params = {'limit': 1, 'offset': 1, 'total_count': True}
        params, headers = usage_examples.authorize_request(params, base_headers)
        res = web_app.get(resource_url, params=params, headers=headers)
        assert res.headers['X-Total-Count'] == str(total_count)
        embedded = list(res.json_body['_embedded'].values())[0]
        assert len(embedded) == 1

    params = {'embedded': False}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    params = {'embedded': False, 'total_count': True}
    params, headers = usage_examples.authorize_request(params, base_headers)
    res = web_app.get(resource_url, params=params, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    ValidationError = usage_examples.ValidationError

    if is_offset_paging:
        params = {'offset': 'off', 'limit': 'lim'}
        params, headers = usage_examples.authorize_request(params, base_headers)
        web_app.get(
            resource_url, params=params, headers=headers,
            exception=ValidationError({
                'limit': '"lim" is not a number',
                'offset': '"off" is not a number'
            })
        )

        params = {'offset': -1, 'limit': -1}
        params, headers = usage_examples.authorize_request(params, base_headers)
        web_app.get(
            resource_url, params=params, headers=headers,
            exception=ValidationError({
                'limit': '-1 is less than minimum value 0',
                'offset': '-1 is less than minimum value 0'
            })
        )
    else:
        params = {'limit': 'lim'}
        params, headers = usage_examples.authorize_request(params, base_headers)
        web_app.get(
            resource_url, params=params, headers=headers,
            exception=ValidationError({'limit': '"lim" is not a number'})
        )

        params = {'limit': -1}
        params, headers = usage_examples.authorize_request(params, base_headers)
        web_app.get(
            resource_url, params=params, headers=headers,
            exception=ValidationError({'limit': '-1 is less than minimum value 0'})
        )
