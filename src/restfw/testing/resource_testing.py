# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from copy import deepcopy
from typing import Dict

from pyramid.httpexceptions import HTTPException
from webtest.forms import Upload
from zope.interface import implementer

from ..interfaces import IHalResourceWithEmbedded, ISendTestingRequest
from ..schemas import LISTING_CONF


DEFAULT = object()


class RequestsTester(object):

    def __init__(self, web_app, resource_url):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type resource_url: str
        """
        self.web_app = web_app
        self.resource_url = resource_url
        self.calls_count = 0

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        raise NotImplementedError


@implementer(ISendTestingRequest)
class GetRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        res = self.web_app.get(self.resource_url, params=params, headers=headers,
                               exception=exception, status=status)
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result
        head_res = self.web_app.head(self.resource_url, params=params, headers=headers,
                                     exception=exception, status=status)
        assert head_res.headers == res.headers
        assert head_res.body == b''


@implementer(ISendTestingRequest)
class PutRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        put_method = self.web_app.put_json
        if params and any(isinstance(v, Upload) for v in params.values()):
            put_method = self.web_app.put
        res = put_method(self.resource_url, params=params, headers=headers,
                         exception=exception, status=status)
        if status == 201:
            assert 'Location' in res.headers
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result


@implementer(ISendTestingRequest)
class PatchRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        patch_method = self.web_app.patch_json
        if params and any(isinstance(v, Upload) for v in params.values()):
            patch_method = self.web_app.patch
        res = patch_method(self.resource_url, params=params, headers=headers,
                           exception=exception, status=status)
        if status == 201:
            assert 'Location' in res.headers
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result


@implementer(ISendTestingRequest)
class PostRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        post_method = self.web_app.post_json
        if params and any(isinstance(v, Upload) for v in params.values()):
            post_method = self.web_app.post
        res = post_method(self.resource_url, params=params, headers=headers,
                          exception=exception, status=status)
        if status == 201:
            assert 'Location' in res.headers
            assert res.headers['Location']
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result


@implementer(ISendTestingRequest)
class DeleteRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        self.calls_count += 1
        params = params if params is not DEFAULT else {}
        res = self.web_app.delete_json(self.resource_url, params=params, headers=headers,
                                       exception=exception, status=status)
        if status == 204:
            assert res.body == b''
        if result is not None:
            if res.content_type == 'application/json':
                assert res.json_body == result
            else:
                assert res.text == result


def assert_resource(resource_info, web_app):
    """
    :type resource_info: restfw.resource_info.ResourceInfo
    :type web_app: restfw.testing.webapp.WebApp
    """
    info_name = resource_info.__class__.__name__

    # Test GET requests
    send = GetRequestsTester(web_app, resource_info.resource_url)
    if resource_info.get_requests:
        resource_info.get_requests(send)
    if 'GET' in resource_info.allowed_methods:
        assert send.calls_count > 0, '{} has not any GET requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends GET requests to resource'.format(info_name)

    # Test listing of embedded resources
    if (IHalResourceWithEmbedded.providedBy(resource_info.resource) and
            resource_info.test_listing):
        orig_listing_conf = deepcopy(LISTING_CONF)
        try:
            assert_container_listing(resource_info, web_app)
        finally:
            LISTING_CONF.clear()
            LISTING_CONF.update(orig_listing_conf)

    # Test PUT requests
    send = PutRequestsTester(web_app, resource_info.resource_url)
    if resource_info.put_requests:
        resource_info.put_requests(send)
    if 'PUT' in resource_info.allowed_methods:
        assert send.calls_count > 0, '{} has not any PUT requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends PUT requests to resource'.format(info_name)

    # Test PATCH requests
    send = PatchRequestsTester(web_app, resource_info.resource_url)
    if resource_info.patch_requests:
        resource_info.patch_requests(send)
    if 'PATCH' in resource_info.allowed_methods:
        assert send.calls_count > 0, '{} has not any PATCH requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends PATCH requests to resource'.format(info_name)

    # Test POST requests
    send = PostRequestsTester(web_app, resource_info.resource_url)
    if resource_info.post_requests:
        resource_info.post_requests(send)
    if 'POST' in resource_info.allowed_methods:
        assert send.calls_count > 0, '{} has not any POST requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends POST requests to resource'.format(info_name)

    # Test DELETE requests
    send = DeleteRequestsTester(web_app, resource_info.resource_url)
    if resource_info.delete_requests:
        resource_info.delete_requests(send)
    if 'DELETE' in resource_info.allowed_methods:
        assert send.calls_count > 0, '{} has not any DELETE requests'.format(info_name)
    else:
        assert send.calls_count == 0, '{} sends DELETE requests to resource'.format(info_name)


def assert_container_listing(resource_info, web_app):
    """
    :type resource_info: restfw.resource_info.ResourceInfo
    :type web_app: restfw.testing.webapp.WebApp
    """
    LISTING_CONF['max_limit'] = 2
    resource_url = resource_info.resource_url
    headers = resource_info.headers_for_listing

    res = web_app.get(resource_url, headers=headers)
    assert 'X-Total-Count' not in res.headers
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    res = web_app.get(resource_url, params={'total_count': False}, headers=headers)
    assert 'X-Total-Count' not in res.headers

    res = web_app.get(resource_url, params={'total_count': True}, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    next_link = res['_links']['next']['href']
    res = web_app.get(next_link, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 1

    prev_link = res['_links']['prev']['href']
    res = web_app.get(prev_link, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    res = res.json_body
    embedded = list(res['_embedded'].values())[0]
    assert len(embedded) == 2

    # `limit` is less than `max_value_of_limit`
    res = web_app.get(resource_url, params={'limit': 1, 'total_count': True}, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 1

    # `limit` is great than `max_value_of_limit`
    res = web_app.get(resource_url, params={'limit': 10, 'total_count': True}, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 2

    res = web_app.get(resource_url, params={'offset': 2, 'total_count': True}, headers=headers)
    assert res.headers['X-Total-Count'] == '3'
    embedded = list(res.json_body['_embedded'].values())[0]
    assert len(embedded) == 1

    res = web_app.get(resource_url, params={'embedded': False}, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    res = web_app.get(resource_url, params={'embedded': False, 'total_count': True}, headers=headers)
    assert 'X-Total-Count' not in res.headers
    assert '_embedded' not in res.json_body

    ValidationError = resource_info.ValidationError

    web_app.get(resource_url, params={'offset': 'off', 'limit': 'lim'}, headers=headers,
                exception=ValidationError({'limit': '"lim" is not a number',
                                           'offset': '"off" is not a number'}))

    web_app.get(resource_url, params={'offset': -1, 'limit': -1}, headers=headers,
                exception=ValidationError({'limit': '-1 is less than minimum value 0',
                                           'offset': '-1 is less than minimum value 0'}))
