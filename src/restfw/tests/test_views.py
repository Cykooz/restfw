# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 08.09.2016
"""
import uuid

import colander
import pytest
from cykooz.testing import D
from pyramid.security import ALL_PERMISSIONS, Allow, Everyone

from .. import interfaces, schemas, views
from ..hal import HalResource, SimpleContainer
from ..testing import assert_resource
from ..typing import Json
from ..usage_examples import UsageExamples


class DummyHalResource(HalResource):

    def __init__(self, title, description):
        self.title = title
        self.description = description

    def http_put(self, request, params):
        self.title = params['title']
        self.description = params['description']
        return self, False

    def http_delete(self, request, params):
        del self.__parent__[self.__name__]
        return None


class DummyHalResourceSchema(schemas.HalResourceSchema):
    title = schemas.StringNode(title='Resource title', validator=colander.Length(max=50))
    description = schemas.EmptyStringNode(title='Resource description')


class PutDummyHalResourceSchema(colander.MappingSchema):
    title = schemas.StringNode(title='Resource title', validator=colander.Length(max=50))
    description = schemas.EmptyStringNode(title='Resource description', missing='')


class PostDummyHalResourceSchema(PutDummyHalResourceSchema):
    pass


@views.resource_view_config()
class DummyHalResourceView(views.HalResourceView):
    resource: DummyHalResource
    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, DummyHalResourceSchema)

    def as_dict(self) -> Json:
        return {
            'title': self.resource.title,
            'description': self.resource.description,
        }

    options_for_put = interfaces.MethodOptions(PutDummyHalResourceSchema, DummyHalResourceSchema)
    options_for_delete = interfaces.MethodOptions(None, None)


class DummyContainer(SimpleContainer):
    __acl__ = [
        (Allow, Everyone, ALL_PERMISSIONS)
    ]

    def http_post(self, request, params):
        resource = DummyHalResource(params['title'], params['description'])
        res_id = uuid.uuid4().hex
        self[res_id] = resource
        return resource, True


@views.resource_view_config()
class DummyContainerView(views.HalResourceWithEmbeddedView):
    resource: DummyContainer
    options_for_post = interfaces.MethodOptions(PostDummyHalResourceSchema, DummyHalResourceSchema)

    def get_embedded(self, params: dict):
        return views.list_to_embedded_resources(
            self.request, params,
            resources=list(self.resource.values()),
            parent=self.resource,
            embedded_name='items'
        )


class DummyResourceExamples(UsageExamples):

    def prepare_resource(self):
        container = DummyContainer()
        self.root['test_container'] = container
        resource = DummyHalResource('Resource title', 'Resource description')
        container['resource'] = resource
        return resource

    def get_requests(self, send):
        send(
            result={
                '_links': {'self': {'href': self.resource_url}},
                'title': 'Resource title',
                'description': 'Resource description'
            }
        )

    def put_requests(self, send):
        params = {
            'title': 'New title',
            'description': 'New description'
        }
        result = {
            '_links': {'self': {'href': self.resource_url}},
            **params
        }
        send(params=params, result=result)

        send(exception=self.ValidationError({'title': 'Required'}))
        send(
            params={'title': 'T' * 51},
            exception=self.ValidationError({'title': 'Longer than maximum length 50'}),
        )

    def delete_requests(self, send):
        send(status=204)


class DummyContainerExamples(UsageExamples):
    count_of_embedded = 3
    embedded_name = 'items'

    def prepare_resource(self):
        resource = DummyContainer()
        self.root['test_container'] = resource
        for i in range(self.count_of_embedded):
            child = DummyHalResource('Resource title %d' % i,
                                     'Resource description %d' % i)
            resource['res-%d' % i] = child
        return resource

    def get_requests(self, send):
        send(
            result=D({
                '_links': {'self': {'href': 'http://localhost/test_container/'}},
                '_embedded': {
                    'items': [D()] * self.count_of_embedded
                }
            })
        )

    def post_requests(self, send):
        params = {
            'title': 'New title',
            'description': 'New description'
        }
        result = D(params)
        send(params=params, result=result, status=201)

        send(exception=self.ValidationError({'title': 'Required'}))
        send(
            params={'title': 'T' * 51},
            exception=self.ValidationError({'title': 'Longer than maximum length 50'}),
        )


@pytest.fixture(autouse=True)
def register(app_config):
    app_config.scan('restfw.tests.test_views')
    app_config.commit()


def test_resource(web_app, pyramid_request):
    resource_info = DummyResourceExamples(pyramid_request)
    assert_resource(resource_info, web_app)


def test_container(web_app, pyramid_request):
    resource_info = DummyContainerExamples(pyramid_request)
    assert_resource(resource_info, web_app)


def test_resource_views(web_app, pyramid_request):
    container = DummyContainer()
    pyramid_request.root['test_container'] = container
    resource = DummyHalResource('Resource title', 'Resource description')
    container['resource'] = resource
    url = pyramid_request.resource_url(resource)
    res = web_app.get(url)
    assert res.json == {
        '_links': {'self': {'href': url}},
        'title': 'Resource title',
        'description': 'Resource description',
    }

    res = web_app.put_json(url, params={
        'title': 'New title',
        'description': 'New description',
    })
    assert res.json == {
        '_links': {'self': {'href': url}},
        'title': 'New title',
        'description': 'New description',
    }
