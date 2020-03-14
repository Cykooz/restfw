# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 13.12.2017
"""
import itertools

import six
from pyramid.interfaces import ILocation
from pyramid.traversal import quote_path_segment
from zope.interface import implementer

from . import interfaces, schemas
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
        return {'self': {'href': request.resource_url(self)}}

    def __json__(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        result = self.as_dict(request)
        links = self.get_links(request)
        # Add links to sub-resources
        self_url = links['self']['href']
        for name, _ in self.get_sub_resources(request.registry):
            links[name] = {'href': self_url + quote_path_segment(name) + '/'}
        result['_links'] = links
        return result

    def as_embedded(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        result = self.as_dict(request)
        # Embedded version of resource has not links to sub-resources
        result['_links'] = self.get_links(request)
        return result


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
        result = self.__json__(request)
        if params.get('embedded', True):
            embedded = self.get_embedded(request, params)
            if embedded:
                result['_embedded'] = embedded
                result['_links'].update(embedded.paging_links)
        return result


class SimpleContainer(HalResource):

    def __init__(self):
        super(SimpleContainer, self).__init__()
        self.__data = {}

    def __getitem__(self, key):
        try:
            return self.__data[key]
        except KeyError:
            return super(SimpleContainer, self).__getitem__(key)

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


class _IterLength(object):

    def __init__(self, iterable):
        self._iterable = iterable
        self._len = 0

    def __next__(self):
        res = next(self._iterable)
        self._len += 1
        return res

    def get_len(self):
        self._len += sum(1 for _ in self._iterable)
        return self._len


def iter_to_embedded_resources(request, params, iterable, parent, embedded_name):
    offset = params['offset']
    limit = params['limit']
    end = offset + limit + 1
    if params['total_count']:
        iterable = _IterLength(iterable)

    page = list(itertools.islice(iterable, offset, end))
    has_next_page = len(page) > limit
    if has_next_page:
        page.pop(limit - 1)
    paging_links = get_paging_links(parent, request, offset, limit, has_next_page)
    embedded = {embedded_name: page}
    total_count = iterable.get_len() if params['total_count'] else None
    return EmbeddedResources(paging_links, total_count, **embedded)
