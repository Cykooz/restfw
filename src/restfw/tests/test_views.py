# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 08.09.2016
"""
from __future__ import unicode_literals

import uuid

import colander
from mountbit.utils.testing import D
from pyramid.security import ALL_PERMISSIONS, Allow, Everyone

from .. import interfaces, schemas
from ..errors import ValidationError
from ..hal import HalResource, HalResourceWithEmbedded, SimpleContainer, list_to_embedded_resources
from ..testing import assert_resource
from ..usage_examples import UsageExamples


class DummyResourceSchema(schemas.HalResourceSchema):
    title = colander.SchemaNode(colander.String(), title='Resource title',
                                validator=colander.Length(max=50))
    description = colander.SchemaNode(colander.String(allow_empty=True),
                                      title='Resource description')


class PutDummyResourceSchema(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), title='Resource title',
                                validator=colander.Length(max=50))
    description = colander.SchemaNode(colander.String(allow_empty=True),
                                      title='Resource description',
                                      missing='')


class PostDummyResourceSchema(PutDummyResourceSchema):
    pass


class DummyResource(HalResource):

    def __init__(self, title, description):
        super(DummyResource, self).__init__()
        self.title = title
        self.description = description

    def as_dict(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        result = super(DummyResource, self).as_dict(request)
        result['title'] = self.title
        result['description'] = self.description
        return result

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, DummyResourceSchema)
    options_for_put = interfaces.MethodOptions(PutDummyResourceSchema, DummyResourceSchema)
    options_for_delete = interfaces.MethodOptions(None, None)

    def http_put(self, request, params):
        self.title = params['title']
        self.description = params['description']
        return self, False

    def http_delete(self, request, params):
        del self.__parent__[self.__name__]
        return None


class DummyContainer(HalResourceWithEmbedded, SimpleContainer):
    __acl__ = [
        (Allow, Everyone, ALL_PERMISSIONS)
    ]

    def get_links(self, request):
        return HalResource.get_links(self, request)

    def get_embedded(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: EmbeddedResources
        """
        return list_to_embedded_resources(
            request, params,
            resources=list(self.values()),
            parent=self,
            embedded_name='items'
        )

    options_for_post = interfaces.MethodOptions(PostDummyResourceSchema, DummyResourceSchema)

    def http_post(self, request, params):
        resource = DummyResource(params['title'], params['description'])
        res_id = uuid.uuid4().hex
        self[res_id] = resource
        return resource, True


class DummyResourceExamples(UsageExamples):

    def prepare_resource(self):
        container = DummyContainer()
        self.root['test_container'] = container
        resource = DummyResource('Resource title', 'Resource description')
        container['resource'] = resource
        return resource

    def get_requests(self, send):
        result = self.resource.__json__(self.request)
        send(result=result)

    def put_requests(self, send):
        params = {
            'title': 'New title',
            'description': 'New description'
        }
        result = self.resource.__json__(self.request)
        result.update(params)
        send(exception=ValidationError({'title': 'Required'}))
        send(params={'title': 'T' * 51},
             exception=ValidationError({'title': 'Longer than maximum length 50'}))
        send(params=params, result=result)

    def delete_requests(self, send):
        send(status=204)


class DummyContainerExamples(UsageExamples):

    count_of_embedded = 3
    embedded_name = 'items'

    def prepare_resource(self):
        resource = DummyContainer()
        self.root['test_container'] = resource
        for i in range(self.count_of_embedded):
            child = DummyResource('Resource title %d' % i,
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
        send(exception=ValidationError({'title': 'Required'}))
        send(params={'title': 'T' * 51},
             exception=ValidationError({'title': 'Longer than maximum length 50'}))
        send(params=params, result=result, status=201)


def test_resource(web_app, pyramid_request):
    resource_info = DummyResourceExamples(pyramid_request)
    assert_resource(resource_info, web_app)


def test_container(web_app, pyramid_request):
    resource_info = DummyContainerExamples(pyramid_request)
    assert_resource(resource_info, web_app)
