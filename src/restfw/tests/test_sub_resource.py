# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.06.2018
"""
import pytest
from mountbit.utils.testing import D
from pyramid.config import Configurator
from restfw.hal import HalResourceWithEmbedded, SimpleContainer, list_to_embedded_resources
from restfw.resources import add_sub_resource_fabric

from ..hal import HalResource
from ..resources import sub_resource_config


class DummyResource(HalResource):
    pass


@sub_resource_config('sub', DummyResource)
class SubDummyResource(HalResource):

    def __init__(self, parent):
        pass

    def as_dict(self, request):
        return {'title': 'Sub resource'}


class Container(SimpleContainer, HalResourceWithEmbedded):

    def get_embedded(self, request, params):
        return list_to_embedded_resources(
            request, params,
            resources=list(self.values()),
            parent=self,
            embedded_name='items'
        )


def test_add_sub_resource_fabric_directive(app_config, pyramid_request):
    root = pyramid_request.root
    root['resource'] = DummyResource()

    with pytest.raises(KeyError):
        _ = root['resource']['sub']

    app_config.add_sub_resource_fabric(SubDummyResource, 'sub', DummyResource)
    sub = root['resource']['sub']
    assert isinstance(sub, SubDummyResource)
    assert sub.__parent__ is root['resource']
    assert sub.__name__ == 'sub'


def test_sub_resource_config_decorator(app_config, pyramid_request):
    root = pyramid_request.root
    root['resource'] = DummyResource()

    with pytest.raises(KeyError):
        _ = root['resource']['sub']

    app_config.scan('restfw.tests.test_sub_resource')
    sub = root['resource']['sub']
    assert isinstance(sub, SubDummyResource)
    assert sub.__parent__ is root['resource']
    assert sub.__name__ == 'sub'


def test_links_to_sub_resource(web_app):
    root = web_app.root
    root['container'] = container = Container()
    container['resource'] = DummyResource()

    config = Configurator(registry=web_app.registry)
    add_sub_resource_fabric(config, SubDummyResource, 'sub', DummyResource)

    # Get self resource
    res = web_app.get('container/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
            'sub': {'href': 'http://localhost/container/resource/sub/'},
        }
    }

    # Get resource as embedded
    res = web_app.get('container')
    assert res.json_body == D({
        '_embedded': {
            'items': [
                {
                    '_links': {
                        'self': {'href': 'http://localhost/container/resource/'},
                        # Link to sub-resource is absent
                    },
                }
            ]
        }
    })
