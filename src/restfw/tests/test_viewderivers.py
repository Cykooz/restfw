# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 27.12.2019
"""
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.security import ALL_PERMISSIONS, Allow, Everyone
from pyramid.view import view_config

from .. import schemas
from ..errors import ResultValidationError
from ..interfaces import MethodOptions
from ..resources import Resource


class DummySchema(schemas.MappingSchema):
    foo = schemas.StringNode()
    bar = schemas.IntegerNode()


class DummyEditSchema(schemas.MappingSchema):
    foo = schemas.StringNode()
    bar = schemas.IntegerNode()


class DummyResource(Resource):

    __acl__ = [
        (Allow, Everyone, ALL_PERMISSIONS)
    ]

    def __init__(self, model):
        super(DummyResource, self).__init__()
        self.model = model

    options_for_get = MethodOptions(None, DummySchema, permission='get')

    def as_dict(self, request):
        return self.model

    options_for_put = MethodOptions(DummyEditSchema, DummySchema, permission='put')

    def http_put(self, request, params):
        self.model = params
        return self, False


@view_config(name='custom_view', request_method={'GET', 'PATCH'},
             context=DummyResource, permission='patch')
def custom_view(context, request):
    context.model = {'custom': 'view', 'result': 789}
    return context.model


def test_check_request_method_view(web_app, pyramid_request, app_config):
    app_config.scan('restfw.tests.test_viewderivers')
    app_config.commit()

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


def test_check_result_schema(web_app, pyramid_request, app_config):
    app_config.scan('restfw.tests.test_viewderivers')
    app_config.commit()

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
