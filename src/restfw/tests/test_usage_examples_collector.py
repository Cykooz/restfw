# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 04.02.2019
"""
import logging

from mountbit.utils.testing import ANY, D
from pyramid import httpexceptions
from pyramid.security import Allow, Everyone

from .. import schemas
from ..hal import HalResource, SimpleContainer
from ..interfaces import MethodOptions
from ..testing import basic_auth_value
from ..usage_examples import UsageExamples
from ..usage_examples.collector import UsageExamplesCollector
from ..usage_examples.utils import sphinx_doc_filter
from ..utils import get_object_fullname


# Schemas

class DummySchema(schemas.HalResourceSchema):
    value = schemas.IntegerNode(title='Some value')


class PutDummySchema(schemas.MappingSchema):
    value = schemas.IntegerNode(title='Some value')


# Resources

class DummyResource(HalResource):
    """
    Narrative documentation
    =======================

    Some info about
    DummyResource number.
    """

    __acl__ = [
        (Allow, Everyone, 'get'),
        (Allow, 'auth_user', 'dummy.edit'),
    ]

    def __init__(self):
        self.value = 0

    options_for_get = MethodOptions(None, DummySchema)

    def as_dict(self, request):
        return {'value': self.value}

    options_for_put = MethodOptions(PutDummySchema, DummySchema, permission='dummy.edit')

    def http_put(self, request, params):
        """Replace resource with new version.
        :param request: Pyramid's request
        :type request: pyramid.request.Request
        :param params: Dictionary with input arguments
        :type params: dict
        :return: Changed resource
        :rtype: tuple[DummyResource, bool]

        In some cases this method produce magic ether.
        """
        self.value = params['value']
        return self, False


class DummyContainer(SimpleContainer):
    pass


# Usage examples

class Dummy1Examples(UsageExamples):
    """
    This is a first entry point for
    DummyResource.
    """

    def prepare_resource(self):
        container = SimpleContainer()
        container['dummy1'] = DummyResource()
        self.root['container'] = container
        return self.root['container']['dummy1']

    def get_requests(self, send):
        send(
            result={
                '_links': {
                    'self': {'href': 'http://localhost/container/dummy1/'}
                },
                'value': 0
            },
        )

    def put_requests(self, send):
        send(exception=httpexceptions.HTTPUnauthorized)
        send(
            headers={'Authorization': basic_auth_value('other_user', '123')},
            exception=httpexceptions.HTTPForbidden
        )

        params = {'value': 10}
        headers = {'Authorization': basic_auth_value('auth_user', '123')}
        send(
            params=params,
            headers=headers,
            result=D(params),
        )

        send(
            params={'value': 'foo'},
            headers=headers,
            exception=self.ValidationError({
                'value': '"foo" is not a number'
            })
        )


class Dummy2Examples(Dummy1Examples):

    def prepare_resource(self):
        container = DummyContainer()
        container['dummy2'] = DummyResource()
        self.root['dummy_container'] = container
        return self.root['dummy_container']['dummy2']

    def get_requests(self, send):
        send(
            result={
                '_links': {
                    'self': {'href': 'http://localhost/dummy_container/dummy2/'}
                },
                'value': 0
            },
        )


class DummyContainerExamples(UsageExamples):

    def prepare_resource(self):
        container = DummyContainer()
        container['dummy'] = DummyResource()
        self.root['dummy_container'] = container
        return self.root['dummy_container']

    def get_requests(self, send):
        send(
            result={
                '_links': {
                    'self': {'href': 'http://localhost/dummy_container/'},
                    'dummy': {'href': 'http://localhost/dummy_container/dummy/'},
                },
                'value': 0
            },
        )


def _prepare_env(request):
    root = request.root
    keys = list(root.keys())
    for key in keys:
        del root[key]


def test_usage_examples_collector(web_app, app_config):
    logger = logging.getLogger('test_usage_examples_collector')
    logging.disable(logging.CRITICAL)

    collector = UsageExamplesCollector(
        web_app,
        prepare_env=_prepare_env,
        docstring_filter=sphinx_doc_filter,
        logger=logger
    )
    collector.collect()
    assert collector.resources_info == {}
    assert collector.entry_points_info == {}
    assert collector.url_to_ep_id == {}

    # Register usage examples fabrics
    app_config.add_usage_examples_fabric(Dummy1Examples)
    app_config.add_usage_examples_fabric(Dummy2Examples)
    app_config.add_usage_examples_fabric(DummyContainerExamples)
    app_config.commit()
    # and collect again
    collector.collect()

    dummy_class_name = get_object_fullname(DummyResource)
    dummy_usage1_id = get_object_fullname(Dummy1Examples)
    dummy_usage2_id = get_object_fullname(Dummy2Examples)
    container_class_name = get_object_fullname(DummyContainer)
    container_usage_id = get_object_fullname(DummyContainerExamples)

    assert collector.resources_info == {
        dummy_class_name: ANY,
        container_class_name: ANY,
    }
    assert collector.entry_points_info == {
        dummy_usage1_id: ANY,
        dummy_usage2_id: ANY,
        container_usage_id: ANY,
    }
    assert collector.url_to_ep_id == {
        'container/dummy1': dummy_usage1_id,
        'dummy_container/dummy2': dummy_usage2_id,
        'dummy_container': container_usage_id,
    }

    # DummyResource Info
    info = collector.resources_info[dummy_class_name]
    assert info.count_of_entry_points == 2
    assert info.class_name == dummy_class_name
    assert info.description == [
        'Narrative documentation',
        '=======================',
        '',
        'Some info about',
        'DummyResource number.',
    ]

    # DummyContainer Info
    info = collector.resources_info[container_class_name]
    assert info.count_of_entry_points == 1
    assert info.class_name == container_class_name
    assert info.description == []

    # Dummy Entry Point 1 info
    ep_info = collector.entry_points_info[dummy_usage1_id]
    assert ep_info.name == 'Dummy1'
    assert ep_info.resource_class_name == dummy_class_name
    assert ep_info.description == [
        'This is a first entry point for',
        'DummyResource.'
    ]
    assert len(ep_info.url_elements) == 2
    assert ep_info.url_elements[0].value == 'container'
    assert ep_info.url_elements[0].resource_class_name == get_object_fullname(SimpleContainer)
    assert ep_info.url_elements[0].ep_id is None
    assert ep_info.url_elements[1].value == 'dummy1'
    assert ep_info.url_elements[1].resource_class_name == dummy_class_name
    assert ep_info.url_elements[1].ep_id == dummy_usage1_id

    # Methods of Dummy Entry Point 1...
    methods = ep_info.methods
    assert list(methods.keys()) == ['GET', 'PUT']
    # ... GET
    method = methods['GET']
    assert method.description == [
        'Returns a resource, any of it representation or any response instance.'
    ]
    assert method.allowed_principals == {Everyone}
    assert method.input_schema is None
    assert method.output_schema is not None
    assert method.output_schema.class_name == get_object_fullname(DummySchema)
    assert len(method.examples_info) == 1
    assert [ei.response_info.status_code for ei in method.examples_info] == [200]
    # ... PUT
    method = methods['PUT']
    assert method.description == [
        'Replace resource with new version.',
        '',
        'In some cases this method produce magic ether.',
    ]
    assert method.allowed_principals == {'auth_user'}
    assert method.input_schema is not None
    assert method.input_schema.class_name == get_object_fullname(PutDummySchema)
    assert method.output_schema is not None
    assert method.output_schema.class_name == get_object_fullname(DummySchema)
    assert len(method.examples_info) == 4
    assert [ei.response_info.status_code for ei in method.examples_info] == [401, 403, 200, 422]

    # Dummy Entry Point 2 info
    ep_info = collector.entry_points_info[dummy_usage2_id]
    assert ep_info.name == 'Dummy2'
    assert ep_info.resource_class_name == dummy_class_name
    assert ep_info.description == []  # docstrings do not inherits
    assert len(ep_info.url_elements) == 2
    assert ep_info.url_elements[0].value == 'dummy_container'
    assert ep_info.url_elements[0].resource_class_name == container_class_name
    assert ep_info.url_elements[0].ep_id == container_usage_id
    assert ep_info.url_elements[1].value == 'dummy2'
    assert ep_info.url_elements[1].resource_class_name == dummy_class_name
    assert ep_info.url_elements[1].ep_id == dummy_usage2_id
