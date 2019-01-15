# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 15.01.2019
"""
from pyramid import httpexceptions

from restfw.hal import HalResource


class DummyResource(HalResource):

    def __init__(self, exception):
        super(DummyResource, self).__init__()
        self.exception = exception

    def http_get(self, request, params):
        raise self.exception


def test_http_exception_view(web_app, pyramid_request):
    root = pyramid_request.root

    root['404'] = DummyResource(httpexceptions.HTTPNotFound('Message'))
    res = web_app.get(pyramid_request.resource_url(root['404']), check_response=False)
    assert res.status_int == 404
    assert res.content_type == 'application/json'
    assert res.json_body == {
        'code': 'NotFound',
        'description': 'The resource could not be found.',
        'detail': {'msg': 'Message'}
    }

    root['304'] = DummyResource(httpexceptions.HTTPNotModified())
    res = web_app.get(pyramid_request.resource_url(root['304']), check_response=False)
    assert res.status_int == 304
    assert 'Content-Type' not in res.headers
    assert 'Content-Length' not in res.headers
    assert res.content_type is None
    assert res.content_length is None
    assert res.body == b''
