# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.11.2018
"""

import pytest
from cykooz.testing import D
from pyramid.traversal import find_interface

from ..hal import HalResource, SimpleContainer
from ..views import (
    HalResourceWithEmbeddedView,
    list_to_embedded_resources,
    resource_view_config,
)


class DummyApiVersion(SimpleContainer):
    pass


class DummyMinApiVersion:
    """Testing predicate for sub resource fabric"""

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
    """Testing predicate for sub resource fabric"""

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


class SubDummyResource(HalResource):
    def __init__(self, parent):
        pass


class Sub1DummyResource(HalResource):
    def __init__(self, parent):
        pass


class Sub2DummyResource(HalResource):
    def __init__(self, parent):
        pass


class Sub23DummyResource(HalResource):
    def __init__(self, parent):
        pass


class Container(SimpleContainer):
    pass


@resource_view_config(Container)
class ContainerView(HalResourceWithEmbeddedView):
    def get_embedded(self, params: dict):
        return list_to_embedded_resources(
            self.request,
            params,
            resources=list(self.resource.values()),
            parent=self.resource,
            embedded_name='items',
        )


@pytest.fixture(name='root')
def root_fixture(app_config, pyramid_request):
    root = pyramid_request.root
    root['container'] = Container()
    root['container']['resource'] = DummyResource()
    for i in range(4):
        root[str(i)] = DummyApiVersion()
        root[str(i)]['resource'] = DummyResource()

    app_config.add_sub_resource_fabric_predicate('min_api_version', DummyMinApiVersion)
    app_config.add_sub_resource_fabric_predicate('max_api_version', DummyMaxApiVersion)

    app_config.add_sub_resource_fabric(SubDummyResource, 'sub', DummyResource)
    app_config.add_sub_resource_fabric(
        SubDummyResource, 'static_sub', DummyResource, add_link_into_embedded=True
    )
    app_config.add_sub_resource_fabric(
        Sub1DummyResource, 'sub1', DummyResource, min_api_version=1
    )
    app_config.add_sub_resource_fabric(
        Sub2DummyResource, 'sub2', DummyResource, max_api_version=2
    )
    app_config.add_sub_resource_fabric(
        Sub23DummyResource,
        'sub23',
        DummyResource,
        add_link_into_embedded=True,
        min_api_version=2,
        max_api_version=3,
    )
    app_config.scan('restfw.tests.test_add_sub_resource_fabric')
    app_config.commit()
    return root


def test_add_sub_resource_fabric_directive(root):
    sub = root['container']['resource']['sub']
    assert isinstance(sub, SubDummyResource)
    assert sub.__parent__ is root['container']['resource']
    assert sub.__name__ == 'sub'

    with pytest.raises(KeyError):
        _ = root['0']['resource']['sub1']
    for v in [1, 2, 3]:
        sub1 = root[str(v)]['resource']['sub1']
        assert isinstance(sub1, Sub1DummyResource)

    with pytest.raises(KeyError):
        _ = root['3']['resource']['sub2']
    for v in [0, 1, 2]:
        sub2 = root[str(v)]['resource']['sub2']
        assert isinstance(sub2, Sub2DummyResource)

    for v in [0, 1]:
        with pytest.raises(KeyError):
            _ = root[str(v)]['resource']['sub23']
    for v in [2, 3]:
        sub23 = root[str(v)]['resource']['sub23']
        assert isinstance(sub23, Sub23DummyResource)


def test_links_to_sub_resource(web_app, root, app_config):
    # Get self resource
    res = web_app.get('container/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
            'sub': {'href': 'http://localhost/container/resource/sub/'},
            'static_sub': {'href': 'http://localhost/container/resource/static_sub/'},
        }
    }

    # Get resource as embedded
    res = web_app.get('container')
    assert res.json_body == D(
        {
            '_embedded': {
                'items': [
                    {
                        '_links': {
                            'self': {'href': 'http://localhost/container/resource/'},
                            # Only static link to sub-resource has added
                            'static_sub': {
                                'href': 'http://localhost/container/resource/static_sub/'
                            },
                        },
                    }
                ]
            }
        }
    )

    # Get different api versions
    res = web_app.get('0/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/0/resource/'},
            'sub': {'href': 'http://localhost/0/resource/sub/'},
            'sub2': {'href': 'http://localhost/0/resource/sub2/'},
            'static_sub': {'href': 'http://localhost/0/resource/static_sub/'},
        }
    }
    res = web_app.get('1/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/1/resource/'},
            'sub': {'href': 'http://localhost/1/resource/sub/'},
            'sub1': {'href': 'http://localhost/1/resource/sub1/'},
            'sub2': {'href': 'http://localhost/1/resource/sub2/'},
            'static_sub': {'href': 'http://localhost/1/resource/static_sub/'},
        }
    }
    res = web_app.get('2/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/2/resource/'},
            'sub': {'href': 'http://localhost/2/resource/sub/'},
            'sub1': {'href': 'http://localhost/2/resource/sub1/'},
            'sub2': {'href': 'http://localhost/2/resource/sub2/'},
            'sub23': {'href': 'http://localhost/2/resource/sub23/'},
            'static_sub': {'href': 'http://localhost/2/resource/static_sub/'},
        }
    }
    res = web_app.get('3/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/3/resource/'},
            'sub': {'href': 'http://localhost/3/resource/sub/'},
            'sub1': {'href': 'http://localhost/3/resource/sub1/'},
            'sub23': {'href': 'http://localhost/3/resource/sub23/'},
            'static_sub': {'href': 'http://localhost/3/resource/static_sub/'},
        }
    }
