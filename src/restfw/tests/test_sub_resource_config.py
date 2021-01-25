# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.06.2018
"""
import pytest
from pyramid.traversal import find_interface

from ..hal import HalResource, SimpleContainer
from ..resources import sub_resource_config
from ..views import HalResourceWithEmbeddedView, list_to_embedded_resources, resource_view_config


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


@sub_resource_config('sub', DummyResource)
class SubDummyResource(HalResource):
    def __init__(self, parent):
        pass


@sub_resource_config('sub1', DummyResource, min_api_version=1)
class Sub1DummyResource(HalResource):
    def __init__(self, parent):
        pass


@sub_resource_config('sub2', DummyResource, max_api_version=2)
class Sub2DummyResource(HalResource):
    def __init__(self, parent):
        pass


@sub_resource_config('sub23', DummyResource, min_api_version=2, max_api_version=3)
class Sub23DummyResource(HalResource):
    def __init__(self, parent):
        pass


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

    app_config.add_sub_resource_fabric_predicate('min_api_version', DummyMinApiVersion)
    app_config.add_sub_resource_fabric_predicate('max_api_version', DummyMaxApiVersion)
    return root


def test_sub_resource_config_decorator(app_config, root):
    with pytest.raises(KeyError):
        _ = root['container']['resource']['sub']

    app_config.scan('restfw.tests.test_sub_resource_config')
    with pytest.raises(KeyError):
        _ = root['container']['resource']['sub']
    app_config.commit()

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
