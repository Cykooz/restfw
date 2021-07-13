# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 27.12.2019
"""
import pytest
from pyramid.authorization import ALL_PERMISSIONS, Allow, Everyone
from pyramid.httpexceptions import HTTPMethodNotAllowed, HTTPNotModified, HTTPPreconditionFailed
from pyramid.view import view_config

from .. import schemas
from ..errors import ResultValidationError
from ..interfaces import MethodOptions
from ..resources import Resource
from ..typing import Json
from ..utils import ETag
from ..views import ResourceView, resource_view_config


class DummySchema(schemas.MappingNode):
    foo = schemas.StringNode()
    bar = schemas.IntegerNode()


class DummyEditSchema(schemas.MappingNode):
    foo = schemas.StringNode()
    bar = schemas.IntegerNode()


class DummyResource(Resource):
    __acl__ = [
        (Allow, Everyone, ALL_PERMISSIONS)
    ]

    def __init__(self, model):
        self.model = model
        self.etag = None

    def get_etag(self):
        return self.etag

    def as_dict(self, request):
        return self.model

    def http_put(self, request, params):
        self.model = params
        return False


@resource_view_config(DummyResource)
class DummyResourceView(ResourceView):
    options_for_get = MethodOptions(None, DummySchema, permission='get')
    options_for_put = MethodOptions(DummyEditSchema, DummySchema, permission='put')

    def as_dict(self) -> Json:
        return self.resource.model


@view_config(name='custom_view', request_method={'GET', 'PATCH'},
             context=DummyResource, permission='patch')
def custom_view(context, request):
    context.model = {'custom': 'view', 'result': 789}
    return context.model


@pytest.fixture(autouse=True)
def register(app_config):
    app_config.scan('restfw.tests.test_viewderivers')
    app_config.commit()


def test_check_request_method_view(web_app, pyramid_request):
    root = pyramid_request.root
    root['resource'] = DummyResource({'foo': 'Hello', 'bar': 123})
    resource_url = pyramid_request.resource_url(root['resource'])

    res = web_app.get(resource_url)
    assert res.content_type == 'application/json'
    assert res.json_body == {'foo': 'Hello', 'bar': 123}

    params = {'foo': 'World', 'bar': 456}
    res = web_app.put_json(resource_url, params=params)
    assert res.json_body == params

    web_app.post_json(resource_url, params=params, exception=HTTPMethodNotAllowed())
    web_app.delete_json(resource_url, params=params, exception=HTTPMethodNotAllowed())
    web_app.patch_json(resource_url, params=params, exception=HTTPMethodNotAllowed())

    # View deriver do not work for custom views
    custom_view_url = resource_url + 'custom_view'
    res = web_app.patch_json(custom_view_url)
    assert res.json_body == {'custom': 'view', 'result': 789}


def test_check_result_schema(web_app, pyramid_request):
    root = pyramid_request.root
    root['resource'] = resource = DummyResource({'foo': 'Hello', 'bar': 123})
    resource_url = pyramid_request.resource_url(root['resource'])

    res = web_app.get(resource_url)
    assert res.json_body == {'foo': 'Hello', 'bar': 123}

    resource.model = {'bad': 'result'}
    web_app.get(resource_url, exception=ResultValidationError({'foo': 'Required', 'bar': 'Required'}))

    # View deriver do not work for custom views
    custom_view_url = resource_url + 'custom_view'
    res = web_app.get(custom_view_url)
    assert res.json_body == {'custom': 'view', 'result': 789}


@pytest.mark.parametrize(
    ['etag', 'if_match', 'if_none_match', 'status_code'],
    [
        (None, None, None, 200),
        (None, '*', None, 200),
        (None, '"etag"', None, 412),
        (None, None, '"etag"', 200),
        (None, None, '*', 200),

        (ETag('etag'), None, None, 200),
        (ETag('etag'), '*', None, 200),
        (ETag('etag'), '"etag"', None, 200),
        (ETag('etag'), '"other", "etag"', None, 200),
        (ETag('etag'), '"other"', None, 412),
        (ETag('etag'), 'W/"etag"', None, 412),

        (ETag('etag', False), None, None, 200),
        (ETag('etag', False), '*', None, 200),
        (ETag('etag', False), '"etag"', None, 412),
        (ETag('etag', False), '"other", "etag"', None, 412),
        (ETag('etag', False), '"other"', None, 412),
        (ETag('etag', False), 'W/"etag"', None, 412),

        (ETag('etag'), None, '"etag"', 304),
        (ETag('etag'), None, '"other", "etag"', 304),
        (ETag('etag'), None, 'W/"etag"', 304),
        (ETag('etag'), None, '"other", W/"etag"', 304),
        (ETag('etag'), None, '*', 304),
        (ETag('etag'), None, '"other"', 200),

        (ETag('etag', False), None, '"etag"', 304),
        (ETag('etag', False), None, '"other", "etag"', 304),
        (ETag('etag', False), None, 'W/"etag"', 304),
        (ETag('etag', False), None, '"other", W/"etag"', 304),
        (ETag('etag', False), None, '*', 304),
        (ETag('etag', False), None, '"other"', 200),

        (ETag('etag'), '"etag"', '"etag"', 304),
        (ETag('etag'), '"etag"', 'W/"etag"', 304),
        (ETag('etag'), '"etag"', '"other"', 200),
        (ETag('etag'), 'W/"etag"', '"etag"', 412),
        (ETag('etag'), 'W/"etag"', '"other"', 412),
    ]
)
def test_process_conditional_get_head_requests(web_app, pyramid_request,
                                               etag, if_match, if_none_match, status_code):
    root = pyramid_request.root
    root['resource'] = resource = DummyResource({'foo': 'Hello', 'bar': 123})
    resource.etag = etag
    resource_url = pyramid_request.resource_url(root['resource'])

    headers = {}
    if if_match:
        headers['If-Match'] = if_match
    if if_none_match:
        headers['If-None-Match'] = if_none_match

    kwargs = {'headers': headers}
    if status_code == 304:
        kwargs['exception'] = HTTPNotModified()
    elif status_code == 412:
        kwargs['exception'] = HTTPPreconditionFailed({'etag': None if etag is None else etag.serialize()})
    else:
        kwargs['status'] = status_code

    web_app.get(resource_url, **kwargs)


@pytest.mark.parametrize(
    ['etag', 'if_match', 'if_none_match', 'status_code'],
    [
        (None, None, None, 200),
        (None, '*', None, 200),
        (None, '"etag"', None, 412),
        (None, None, '"etag"', 200),
        (None, None, '*', 200),

        (ETag('etag'), None, None, 200),
        (ETag('etag'), '*', None, 200),
        (ETag('etag'), '"etag"', None, 200),
        (ETag('etag'), '"other", "etag"', None, 200),
        (ETag('etag'), '"other"', None, 412),
        (ETag('etag'), 'W/"etag"', None, 412),

        (ETag('etag', False), None, None, 200),
        (ETag('etag', False), '*', None, 200),
        (ETag('etag', False), '"etag"', None, 412),
        (ETag('etag', False), '"other", "etag"', None, 412),
        (ETag('etag', False), '"other"', None, 412),
        (ETag('etag', False), 'W/"etag"', None, 412),

        (ETag('etag'), None, '"etag"', 412),
        (ETag('etag'), None, '"other", "etag"', 412),
        (ETag('etag'), None, 'W/"etag"', 412),
        (ETag('etag'), None, '"other", W/"etag"', 412),
        (ETag('etag'), None, '*', 412),
        (ETag('etag'), None, '"other"', 200),

        (ETag('etag', False), None, '"etag"', 412),
        (ETag('etag', False), None, '"other", "etag"', 412),
        (ETag('etag', False), None, 'W/"etag"', 412),
        (ETag('etag', False), None, '"other", W/"etag"', 412),
        (ETag('etag', False), None, '*', 412),
        (ETag('etag', False), None, '"other"', 200),

        (ETag('etag'), '"etag"', '"etag"', 412),
        (ETag('etag'), '"etag"', 'W/"etag"', 412),
        (ETag('etag'), '"etag"', '"other"', 200),
        (ETag('etag'), 'W/"etag"', '"etag"', 412),
        (ETag('etag'), 'W/"etag"', '"other"', 412),
    ]
)
def test_process_conditional_put_requests(web_app, pyramid_request,
                                          etag, if_match, if_none_match, status_code):
    root = pyramid_request.root
    root['resource'] = resource = DummyResource({'foo': 'Hello', 'bar': 123})
    resource.etag = etag
    resource_url = pyramid_request.resource_url(root['resource'])

    headers = {}
    if if_match:
        headers['If-Match'] = if_match
    if if_none_match:
        headers['If-None-Match'] = if_none_match

    kwargs = {'headers': headers}
    if status_code == 304:
        kwargs['exception'] = HTTPNotModified()
    elif status_code == 412:
        kwargs['exception'] = HTTPPreconditionFailed({'etag': None if etag is None else etag.serialize()})
    else:
        kwargs['status'] = status_code

    new_params = {'foo': 'World', 'bar': 456}
    web_app.put_json(resource_url, params=new_params, **kwargs)
