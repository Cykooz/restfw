# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 08.09.2016
"""
from __future__ import unicode_literals

import uuid
from persistent import Persistent

import colander
import transaction
from mountbit.utils.testing import D
from pyramid.security import Allow, Everyone, ALL_PERMISSIONS

from .. import schemas, interfaces
from ..errors import ValidationError
from ..hal import PersistentContainer, list_to_embedded_resources, HalResource, HalResourceWithEmbedded
from ..resource_info import ParamsResult, ResourceInfo
from ..testing import assert_resource


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


class DummyResource(HalResource, Persistent):

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


class DummyContainer(HalResourceWithEmbedded, PersistentContainer):
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


class DummyResourceInfo(ResourceInfo):

    def prepare_resource(self):
        with transaction.manager:
            container = DummyContainer()
            self.root['test_container'] = container
            resource = DummyResource('Resource title', 'Resource description')
            container['resource'] = resource
        return resource

    @property
    def get_requests(self):
        result = self.resource.__json__(self.request)
        return [
            ParamsResult(result=result)
        ]

    @property
    def put_requests(self):
        params = {
            'title': 'New title',
            'description': 'New description'
        }
        result = self.resource.__json__(self.request)
        result.update(params)
        return [
            ParamsResult(exception=ValidationError({'title': 'Required'})),
            ParamsResult(params={'title': 'T' * 51},
                         exception=ValidationError({'title': 'Longer than maximum length 50'})),
            ParamsResult(params=params, result=result),
        ]

    @property
    def delete_requests(self):
        return [ParamsResult(status=204)]


class DummyContainerInfo(ResourceInfo):

    count_of_embedded = 3
    embedded_name = 'items'

    def prepare_resource(self):
        with transaction.manager:
            resource = DummyContainer()
            self.root['test_container'] = resource
            for i in range(self.count_of_embedded):
                child = DummyResource('Resource title %d' % i,
                                      'Resource description %d' % i)
                resource['res-%d' % i] = child
        return resource

    @property
    def get_requests(self):
        return [
            ParamsResult(
                result=D({
                    '_links': {'self': {'href': 'http://localhost/test_container/'}},
                    '_embedded': {
                        'items': [D()] * self.count_of_embedded
                    }
                })
            )
        ]

    @property
    def post_requests(self):
        params = {
            'title': 'New title',
            'description': 'New description'
        }
        result = D(params)
        return [
            ParamsResult(exception=ValidationError({'title': 'Required'})),
            ParamsResult(params={'title': 'T' * 51},
                         exception=ValidationError({'title': 'Longer than maximum length 50'})),
            ParamsResult(params=params, result=result, status=201),
        ]


def test_resource(web_app):
    resource_info = DummyResourceInfo(web_app.request)
    assert_resource(resource_info, web_app)


def test_container(web_app):
    resource_info = DummyContainerInfo(web_app.request)
    assert_resource(resource_info, web_app)
