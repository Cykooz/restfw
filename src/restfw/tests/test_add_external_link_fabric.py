# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 17.04.2020
"""
import colander
import pytest
from cykooz.testing import D
from pyramid.traversal import find_interface

from ..hal import HalResource, SimpleContainer
from ..views import HalResourceWithEmbeddedView, get_resource_view, list_to_embedded_resources, resource_view_config


class DummyApiVersion(SimpleContainer):
    pass


class DummyMinApiVersion:
    """A testing predicate for fabric of external link"""

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
    """A testing predicate for fabric of external link"""

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


def dummy_external_link(request, resource):
    return 'http://dummy.com/resource/{id}'


def dummy1_external_link(request, resource):
    return 'http://dummy.com/resource/gte_one'


def dummy2_external_link(request, resource):
    return 'http://dummy.com/resource/lte_two'


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
    app_config.scan('restfw.tests.test_add_external_link_fabric')
    root = pyramid_request.root
    root['container'] = Container()
    root['container']['resource'] = DummyResource()
    for i in range(4):
        root[str(i)] = DummyApiVersion()
        root[str(i)]['resource'] = DummyResource()

    app_config.add_external_link_fabric_predicate('min_api_version', DummyMinApiVersion)
    app_config.add_external_link_fabric_predicate('max_api_version', DummyMaxApiVersion)

    app_config.add_external_link_fabric(
        dummy_external_link, 'ext', DummyResource,
        title='Link to extended resource',
        description='Some description',
        templated=True,
    )
    app_config.add_external_link_fabric(
        dummy1_external_link, 'ext1', DummyResource, min_api_version=1,
        optional=True,
    )
    app_config.add_external_link_fabric(
        dummy2_external_link, 'ext2', DummyResource, max_api_version=2
    )
    app_config.add_external_link_fabric(
        dummy23_external_link, 'ext23', DummyResource, min_api_version=2, max_api_version=3
    )
    app_config.commit()
    return root


def test_external_links(web_app, root, app_config, pyramid_request):
    # Get self resource
    res = web_app.get('container/resource').json_body
    assert res == {
        '_links': {
            'self': {'href': 'http://localhost/container/resource/'},
            'ext': {'href': 'http://dummy.com/resource/{id}', 'templated': True},
        }
    }

    resource = root['container']['resource']
    view = get_resource_view(resource, pyramid_request)
    schema = view.options_for_get.output_schema().bind(
        request=pyramid_request,
        context=resource,
    )
    ext_node = schema.get('_links').get('ext')
    assert ext_node.title == 'Link to extended resource'
    assert ext_node.description == 'Some description'
    assert ext_node.missing == colander.required

    # Get resource as embedded
    res = web_app.get('container')
    assert res.json_body == D({
        '_embedded': {
            'items': [
                {
                    '_links': {
                        'self': {'href': 'http://localhost/container/resource/'},
                        # An external link is absent
                    },
                }
            ]
        }
    })

    # Get different api versions
    res = web_app.get('0/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/0/resource/'},
            'ext': {'href': 'http://dummy.com/resource/{id}', 'templated': True},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
        }
    }

    res = web_app.get('1/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/1/resource/'},
            'ext': {'href': 'http://dummy.com/resource/{id}', 'templated': True},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
        }
    }

    resource = root['1']['resource']
    view = get_resource_view(resource, pyramid_request)
    schema = view.options_for_get.output_schema().bind(
        request=pyramid_request,
        context=resource,
    )
    ext_node = schema.get('_links').get('ext1')
    assert ext_node.missing == colander.drop

    res = web_app.get('2/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/2/resource/'},
            'ext': {'href': 'http://dummy.com/resource/{id}', 'templated': True},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext2': {'href': 'http://dummy.com/resource/lte_two'},
            'ext23': {'href': 'http://dummy.com/resource/lte_two__gte_three'},
        }
    }
    res = web_app.get('3/resource')
    assert res.json_body == {
        '_links': {
            'self': {'href': 'http://localhost/3/resource/'},
            'ext': {'href': 'http://dummy.com/resource/{id}', 'templated': True},
            'ext1': {'href': 'http://dummy.com/resource/gte_one'},
            'ext23': {'href': 'http://dummy.com/resource/lte_two__gte_three'},
        }
    }
