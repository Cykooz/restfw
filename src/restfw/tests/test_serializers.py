"""
:Authors: cykooz
:Date: 11.01.2021
"""

import json

from pyramid.renderers import render

from .. import views
from ..hal import HalResource, SimpleContainer
from ..resources import Resource
from ..typing import Json
from ..utils import open_pyramid_request


class DummyResource(Resource):
    def __init__(self, title, description):
        self.title = title
        self.description = description


class DummyResourceView(views.ResourceView):
    resource: DummyResource

    def as_dict(self) -> Json:
        return {
            'title': self.resource.title,
            'description': self.resource.description,
        }


class DummyHalResource(HalResource):
    def __init__(self, title, description):
        self.title = title
        self.description = description


@views.resource_view_config(DummyHalResource)
class DummyHalResourceView(views.HalResourceView):
    resource: DummyHalResource

    def as_dict(self) -> Json:
        return {
            'title': self.resource.title,
            'description': self.resource.description,
        }

    def as_embedded(self) -> dict:
        return {
            '_links': self.get_links(),
            'title': self.resource.title,
        }


class Container(SimpleContainer):
    pass


@views.resource_view_config(Container)
class ContainerView(views.HalResourceWithEmbeddedView):
    resource: Container

    def as_dict(self) -> Json:
        return {
            'title': 'It is container',
        }

    def get_embedded(self, params: dict):
        return views.list_to_embedded_resources(
            self.request,
            params,
            resources=list(self.resource.values()),
            parent=self.resource,
            embedded_name='items',
        )


# Tests


def test_resource_serializer(pyramid_request, app_config):
    container = SimpleContainer()
    pyramid_request.root['test_container'] = container
    resource = DummyResource('Resource title', 'Resource description')
    container['resource'] = resource

    res = render(None, resource, request=pyramid_request)
    assert res == '{}'

    app_config.add_resource_view(DummyResourceView, resource_class=DummyResource)
    app_config.commit()
    res = render(None, resource, request=pyramid_request)
    assert json.loads(res) == {
        'title': 'Resource title',
        'description': 'Resource description',
    }


def test_hal_resource_serializer(pyramid_request, app_config):
    container = SimpleContainer()
    pyramid_request.root['test_container'] = container
    resource = DummyHalResource('Resource title', 'Resource description')
    container['resource'] = resource
    resource_url = pyramid_request.resource_url(resource)

    res = render(None, resource, request=pyramid_request)
    assert json.loads(res) == {
        '_links': {'self': {'href': resource_url}},
    }

    app_config.scan('restfw.tests.test_serializers')
    app_config.commit()
    res = render(None, resource, request=pyramid_request)
    assert json.loads(res) == {
        '_links': {'self': {'href': resource_url}},
        'title': 'Resource title',
        'description': 'Resource description',
    }


def test_hal_resource_with_embedded_resources(pyramid_request, app_config):
    container = Container()
    pyramid_request.root['container'] = container
    for i in range(3):
        resource = DummyHalResource(f'Resource {i} title', f'Resource {i} description')
        container[f'res{i}'] = resource

    params = {
        'offset': 0,
        'limit': 500,
        'total_count': True,
    }
    url = pyramid_request.resource_url(container, query=params)
    with open_pyramid_request(pyramid_request.registry, url) as request:
        view = views.get_resource_view(container, request)
        res = render(None, view.http_get(), request=request)
        assert json.loads(res) == {
            '_links': {
                'self': {'href': 'http://localhost/container/'},
                'res0': {'href': 'http://localhost/container/res0/'},
                'res1': {'href': 'http://localhost/container/res1/'},
                'res2': {'href': 'http://localhost/container/res2/'},
            },
        }

    # Register custom views
    app_config.scan('restfw.tests.test_serializers')
    app_config.commit()
    with open_pyramid_request(pyramid_request.registry, url) as request:
        view = views.get_resource_view(container, request)
        res = render(None, view.http_get(), request=request)
        assert json.loads(res) == {
            '_links': {
                'self': {'href': 'http://localhost/container/'},
            },
            'title': 'It is container',
            '_embedded': {
                'items': [
                    {
                        '_links': {
                            'self': {'href': 'http://localhost/container/res0/'}
                        },
                        'title': 'Resource 0 title',
                    },
                    {
                        '_links': {
                            'self': {'href': 'http://localhost/container/res1/'}
                        },
                        'title': 'Resource 1 title',
                    },
                    {
                        '_links': {
                            'self': {'href': 'http://localhost/container/res2/'}
                        },
                        'title': 'Resource 2 title',
                    },
                ]
            },
        }
