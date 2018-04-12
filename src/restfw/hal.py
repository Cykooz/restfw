# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 13.12.2017
"""
import six
from pyramid.interfaces import ILocation
from zope.interface import implementer

from . import schemas, interfaces
from .resources import Resource
from .utils import get_paging_links


@implementer(interfaces.IHalResource)
class HalResource(Resource):

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.HalResourceSchema)

    def get_links(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        links = {'self': {'href': request.resource_url(self)}}
        # adapters = request.registry.getAdapters([self], interfaces.IResourceLinks)
        # for adapter in adapters:
        #     links.update(adapter.get_links(request))
        return links

    def __json__(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        result = self.as_dict(request)
        result['_links'] = self.get_links(request)
        return result

    def as_embedded(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        return self.__json__(request)


class EmbeddedResources(object):

    def __init__(self, paging_links=None, total_count=None, **kwargs):
        self.paging_links = paging_links or {}
        self.total_count = total_count
        self.embedded = kwargs

    def __json__(self, request):
        result = {}
        for key, resources in six.iteritems(self.embedded):
            if resources is None:
                continue
            if not isinstance(resources, dict) and hasattr(resources, '__iter__'):
                rendered = []
                for resource in resources:
                    if interfaces.IHalResource.providedBy(resource):
                        resource = resource.as_embedded(request)
                    rendered.append(resource)
            elif interfaces.IHalResource.providedBy(resources):
                rendered = resources.as_embedded(request)
            else:
                rendered = resources
            result[key] = rendered
        if self.total_count is not None:
            request.response.headers['X-Total-Count'] = str(self.total_count)
        return result


@implementer(interfaces.IHalResourceWithEmbedded)
class HalResourceWithEmbedded(HalResource):

    def get_embedded(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: EmbeddedResources
        """
        return EmbeddedResources(total_count=0, items=[])

    options_for_get = interfaces.MethodOptions(schemas.GetEmbeddedSchema, schemas.HalResourceWithEmbeddedSchema)

    def http_get(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: dict
        """
        result = self.as_dict(request)
        result['_links'] = self.get_links(request)
        if params.get('embedded', True):
            embedded = self.get_embedded(request, params)
            if embedded:
                result['_embedded'] = embedded
                result['_links'].update(embedded.paging_links)
        return result


@implementer(interfaces.IContainer)
class SimpleContainer(HalResource):

    def __init__(self):
        super(SimpleContainer, self).__init__()
        self.__data = {}

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        if ILocation.providedBy(value):
            value.__name__ = key
            value.__parent__ = self
        return self.__data.__setitem__(key, value)

    def __delitem__(self, key):
        del self.__data[key]

    def __contains__(self, key):
        return key in self.__data

    def keys(self):
        return self.__data.keys()

    def values(self):
        return self.__data.values()

    def get_links(self, request):
        res = super(SimpleContainer, self).get_links(request)
        self_url = res['self']['href']
        for key in self.__data.keys():
            res[key] = {'href': self_url + key + '/'}
        return res


def list_to_embedded_resources(request, params, resources, parent, embedded_name):
    offset = params['offset']
    limit = params['limit']
    end = offset + limit
    count = len(resources)
    if not isinstance(resources, (list, tuple)):
        resources = list(resources)
    page = resources[offset:end]
    has_next_page = count > end
    paging_links = get_paging_links(parent, request, offset, limit, has_next_page)
    embedded = {embedded_name: page}
    total_count = count if params['total_count'] else None
    return EmbeddedResources(paging_links, total_count, **embedded)
