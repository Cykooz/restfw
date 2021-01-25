# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 18.04.2020
"""
import pytest
from pyramid.traversal import find_interface

from ..external_links import external_link_config
from ..hal import HalResource, SimpleContainer
from ..views import HalResourceWithEmbeddedView, list_to_embedded_resources, resource_view_config


class DummyApiVersion(SimpleContainer):
    pass


class DummyMinApiVersion:
    """Testing predicate for fabric of external link"""

    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'min_api_version = %s' % (self.val,)

    phash = text

    def __call__(self, parent):
        api_version = find_interface(parent, DummyApiVersion)
        if not api_version:
            return False
        version = int(api_version.__name__)
        return version >= self.val


class DummyMaxApiVersion:
    """Testing predicate for fabric of external link"""

    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'max_api_version = %s' % (self.val,)

    phash = text

    def __call__(self, parent):
        api_version = find_interface(parent, DummyApiVersion)
        if not api_version:
            return False
        version = int(api_version.__name__)
        return version <= self.val


class DummyResource(HalResource):
    pass


@external_link_config('ext', DummyResource)
def dummy_external_link(request, resource):
    return 'http://dummy.com/resource'


@external_link_config('ext1', DummyResource, min_api_version=1)
def dummy1_external_link(request, resource):
    return 'http://dummy.com/resource/gte_one'


@external_link_config('ext2', DummyResource, max_api_version=2)
def dummy2_external_link(request, resource):
    return 'http://dummy.com/resource/lte_two'


@external_link_config('ext23', DummyResource, min_api_version=2, max_api_version=3)
def dummy23_external_link(request, resource):
    return 'http://dummy.com/resource/lte_two__gte_three'


class Container(SimpleContainer):
    pass


@resource_view_config(Container)
class ContainerView(HalResourceWithEmbeddedView):

    def get_embedded(self, params: dict):
        return list_to_embedded_resources(
            self.request, params,
            resources=list(self.resource.values()),
            parent=self.resource,
            embedded_name='items'
        )


@pytest.fixture(name='root')
def root_fixture(app_config, pyramid_request):
    root = pyramid_request.root
    root['container'] = Container()
    root['container']['resource'] = DummyResource()
    for i in range(4):
        root[str(i)] = DummyApiVersion()
        root[str(i)]['resource'] = DummyResource()

    app_config.add_external_link_fabric_predicate('min_api_version', DummyMinApiVersion)
    app_config.add_external_link_fabric_predicate('max_api_version', DummyMaxApiVersion)

    app_config.commit()
    return root


def test_external_link_config_decorator(web_app, root, app_config):
    res = web_app.get('container/resource').json_body
    assert res == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
        }
    }

    app_config.scan('restfw.tests.test_external_link_config')
    res = web_app.get('container/resource').json_body
    assert res == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
        }
    }

    app_config.commit()
    res = web_app.get('container/resource').json_body
    assert res == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
            'ext': {'href': 'http://dummy.com/resource'},
        }
    }

    # Get different api versions
    res = web_app.get('0/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/0/resource/'},
            'ext': {'href': 'http://dummy.com/resource'},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
        }
    }
    res = web_app.get('1/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/1/resource/'},
            'ext': {'href': 'http://dummy.com/resource'},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
        }
    }
    res = web_app.get('2/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/2/resource/'},
            'ext': {'href': 'http://dummy.com/resource'},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
            'ext23': {'href': 'http://dummy.com/resource/lte_two__gte_three'},
        }
    }
    res = web_app.get('3/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/3/resource/'},
            'ext': {'href': 'http://dummy.com/resource'},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext23': {'href': 'http://dummy.com/resource/lte_two__gte_three'},
        }
    }
