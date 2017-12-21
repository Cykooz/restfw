# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
from copy import deepcopy

from pyramid.interfaces import IRootFactory
from pyramid.request import Request
from pyramid.threadlocal import get_current_request
from pyramid.traversal import DefaultRootFactory
from webtest.forms import Upload

from ..errors import ValidationError
from ..interfaces import IHalResourceWithEmbedded
from ..schemas import LISTING_CONF


def assert_resource(resource_info, web_app):
    """
    :type resource_info: restfw.resource_info.ResourceInfo
    :type web_app: restfw.testing.webapp.WebApp
    """
    get_requests = resource_info.get_requests
    if get_requests is None:
        assert 'GET' not in resource_info.allowed_methods
    else:
        assert 'GET' in resource_info.allowed_methods
        for pr in get_requests:
            get_res = web_app.get(resource_info.resource_url, params=pr.params, headers=pr.headers,
                                  exception=pr.exception, status=pr.status)
            if pr.result is not None:
                assert get_res.json_body == pr.result
            head_res = web_app.head(resource_info.resource_url, params=pr.params, headers=pr.headers,
                                    exception=pr.exception, status=pr.status)
            assert head_res.headers == get_res.headers
            assert head_res.body == b''

        if IHalResourceWithEmbedded.providedBy(resource_info.resource) and resource_info.test_listing:
            orig_listing_conf = deepcopy(LISTING_CONF)
            try:
                assert_container_listing(resource_info, web_app)
            finally:
                LISTING_CONF.clear()
                LISTING_CONF.update(orig_listing_conf)

    put_requests = resource_info.put_requests
    if put_requests is None:
        assert 'PUT' not in resource_info.allowed_methods
    else:
        assert 'PUT' in resource_info.allowed_methods
        for pr in put_requests:
            put_method = web_app.put_json
            if pr.params and any(isinstance(v, Upload) for v in pr.params.values()):
                put_method = web_app.put
            res = put_method(resource_info.resource_url, params=pr.params, headers=pr.headers,
                             exception=pr.exception, status=pr.status)
            if pr.status == 201:
                assert 'Location' in res.headers
                assert res.headers['Location']
            if pr.result is not None:
                assert res.json_body == pr.result

    patch_requests = resource_info.patch_requests
    if patch_requests is None:
        assert 'PATCH' not in resource_info.allowed_methods
    else:
        assert 'PATCH' in resource_info.allowed_methods
        for pr in patch_requests:
            patch_method = web_app.patch_json
            if pr.params and any(isinstance(v, Upload) for v in pr.params.values()):
                patch_method = web_app.patch
            res = patch_method(resource_info.resource_url, params=pr.params, headers=pr.headers,
                               exception=pr.exception, status=pr.status)
            if pr.status == 201:
                assert 'Location' in res.headers
                assert res.headers['Location']
            if pr.result is not None:
                assert res.json_body == pr.result

    post_requests = resource_info.post_requests
    if post_requests is None:
        assert 'POST' not in resource_info.allowed_methods
    else:
        assert 'POST' in resource_info.allowed_methods
        for pr in post_requests:
            post_method = web_app.post_json
            if pr.params and any(isinstance(v, Upload) for v in pr.params.values()):
                post_method = web_app.post
            res = post_method(resource_info.resource_url, params=pr.params, headers=pr.headers,
                              exception=pr.exception, status=pr.status)
            if pr.status == 201:
                assert 'Location' in res.headers
                assert res.headers['Location']
            if pr.result is not None:
                assert res.json_body == pr.result

    delete_requests = resource_info.delete_requests
    if delete_requests is None:
        assert 'DELETE' not in resource_info.allowed_methods
    else:
        assert 'DELETE' in resource_info.allowed_methods
        for pr in delete_requests:
            res = web_app.delete_json(resource_info.resource_url, params=pr.params, headers=pr.headers,
                                      exception=pr.exception, status=pr.status)
            if pr.status == 204:
                assert res.body == b''
            if pr.result is not None:
                assert res.json_body == pr.result


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


def get_root(request=None):
    request = request or get_current_request()
    if getattr(request, 'root', None) is None:
        root_factory = request.registry.queryUtility(IRootFactory, default=DefaultRootFactory)
        root = root_factory(request)  # Initialise pyramid root
        root.set_request(request)
        request.root = root
    return request.root


def get_root_and_request(registry):
    request = Request.blank('http://localhost/')
    request.registry = registry
    root = get_root(request)
    return root, request
