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

from ..errors import ValidationError
from ..interfaces import IHalResourceWithEmbedded, ISendTestingRequest
from ..resource_info import ResourceInfo
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

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        raise NotImplementedError


@implementer(ISendTestingRequest)
class GetRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        params = params if params is not DEFAULT else {}
        get_res = self.web_app.get(self.resource_url, params=params, headers=headers,
                                   exception=exception, status=status)
        if result is not None:
            assert get_res.json_body == result
        head_res = self.web_app.head(self.resource_url, params=params, headers=headers,
                                     exception=exception, status=status)
        assert head_res.headers == get_res.headers
        assert head_res.body == b''


@implementer(ISendTestingRequest)
class PutRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
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
            assert res.json_body == result


@implementer(ISendTestingRequest)
class PatchRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
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
            assert res.json_body == result


@implementer(ISendTestingRequest)
class PostRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
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
            assert res.json_body == result


@implementer(ISendTestingRequest)
class DeleteRequestsTester(RequestsTester):

    def __call__(self, params=DEFAULT, headers=None, result=None, result_headers=None,
                 exception=None, status=None):
        # type: (Dict, Dict, Dict, Dict, HTTPException, int) -> None
        params = params if params is not DEFAULT else {}
        res = self.web_app.delete_json(self.resource_url, params=params, headers=headers,
                                       exception=exception, status=status)
        if status == 204:
            assert res.body == b''
        if result is not None:
            assert res.json_body == result


def assert_resource(resource_info, web_app):
    """
    :type resource_info: restfw.resource_info.ResourceInfo
    :type web_app: restfw.testing.webapp.WebApp
    """
    try:
        send = GetRequestsTester(web_app, resource_info.resource_url)
        resource_info.get_requests(send)
        assert 'GET' in resource_info.allowed_methods

        if IHalResourceWithEmbedded.providedBy(resource_info.resource) and resource_info.test_listing:
            orig_listing_conf = deepcopy(LISTING_CONF)
            try:
                assert_container_listing(resource_info, web_app)
            finally:
                LISTING_CONF.clear()
                LISTING_CONF.update(orig_listing_conf)
    except NotImplementedError:
        assert 'GET' not in resource_info.allowed_methods

    try:
        send = PutRequestsTester(web_app, resource_info.resource_url)
        resource_info.put_requests(send)
        assert 'PUT' in resource_info.allowed_methods
    except NotImplementedError:
        assert 'PUT' not in resource_info.allowed_methods

    try:
        send = PatchRequestsTester(web_app, resource_info.resource_url)
        resource_info.patch_requests(send)
        assert 'PATCH' in resource_info.allowed_methods
    except NotImplementedError:
        assert 'PATCH' not in resource_info.allowed_methods

    try:
        send = PostRequestsTester(web_app, resource_info.resource_url)
        resource_info.post_requests(send)
        assert 'POST' in resource_info.allowed_methods
    except NotImplementedError:
        assert 'POST' not in resource_info.allowed_methods

    try:
        send = DeleteRequestsTester(web_app, resource_info.resource_url)
        resource_info.delete_requests(send)
        assert 'DELETE' in resource_info.allowed_methods
    except NotImplementedError:
        assert 'DELETE' not in resource_info.allowed_methods


def assert_container_listing(resource_info, web_app):
    # type: (ResourceInfo, WebApp) -> None
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

    web_app.get(resource_url, params={'offset': 'off', 'limit': 'lim'}, headers=headers,
                exception=ValidationError({'limit': '"lim" is not a number',
                                           'offset': '"off" is not a number'}))

    web_app.get(resource_url, params={'offset': -1, 'limit': -1}, headers=headers,
                exception=ValidationError({'limit': '-1 is less than minimum value 0',
                                           'offset': '-1 is less than minimum value 0'}))
