# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 15.01.2019
"""
import pytest
from pyramid import httpexceptions

from .. import views
from ..hal import HalResource, SimpleContainer


class DummyResource(HalResource):

    def __init__(self, exception):
        self.exception = exception


@views.resource_view_config(DummyResource)
class DummyResourceView(views.HalResourceView):
    resource: DummyResource

    def http_get(self):
        raise self.resource.exception


@pytest.fixture(autouse=True)
def register(app_config):
    app_config.scan('restfw.tests.test_exception_views')
    app_config.commit()


def test_http_exception_view(web_app, pyramid_request):
    root = pyramid_request.root

    root['404'] = DummyResource(httpexceptions.HTTPNotFound('Message'))
    res = web_app.get(pyramid_request.resource_url(root['404']), check_response=False)
    assert res.status_int == 404
    assert res.content_type == 'application/json'
    assert res.json_body == {
        'code': 'NotFound',
        'description': 'The resource could not be found.',
        'detail': {'msg': 'Message', 'resource': '/404'}
    }

    root['304'] = DummyResource(httpexceptions.HTTPNotModified())
    res = web_app.get(pyramid_request.resource_url(root['304']), check_response=False)
    assert res.status_int == 304
    assert 'Content-Type' not in res.headers
    assert 'Content-Length' not in res.headers
    assert res.content_type is None
    assert res.content_length is None
    assert res.body == b''


def test_http_not_found_exception(web_app, pyramid_request):
    root = pyramid_request.root
    root['dir'] = SimpleContainer()
    dir_url = pyramid_request.resource_url(root['dir'])

    res = web_app.get(dir_url + 'not_found/sub_resource/child', check_response=False)
    assert res.status_int == 404
    assert res.content_type == 'application/json'
    assert res.json_body == {
        'code': 'NotFound',
        'description': 'The resource could not be found.',
        'detail': {'resource': '/dir/not_found'}
    }
