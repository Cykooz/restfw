# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
import itertools
from typing import Optional, Set, Type, Union, get_type_hints

import venusian
from pyramid import httpexceptions
from pyramid.config import Configurator
from pyramid.interfaces import ILocation
from pyramid.traversal import quote_path_segment
from zope.interface import implementer

from . import interfaces, schemas
from .errors import ParameterError
from .external_links import get_external_links
from .hal import HalResource, SimpleContainer
from .resources import Resource
from .typing import Json, PyramidRequest
from .utils import create_validation_error, get_input_data, get_paging_links


def get_resource_view(resource, request: PyramidRequest) -> Optional['ResourceView']:
    return request.registry.queryMultiAdapter((request, resource), interfaces.IResourceView)


class resource_view_config:
    """A class :term:`decorator` which allows a
    developer to create resource view registrations nearer to it
    definition than use :term:`imperative configuration` to do the same.

    For example, this code in a module ``views.py``::

        from .resources import MyResource

        @views.resource_view_config(MyResource)
        class MyResourceView(views.HalResourceView):
            ...

    Might replace the following call to the
    :meth:`restfw.config.views.add_resource_view` method::

        from .resources import MyResource
        from .views import MyResourceView
        config.add_resource_view(MyResourceView, MyResource)

    Any ``**predicate`` arguments will be passed along to
    :meth:`restfw.config.views.add_resource_view`.

    Two additional keyword arguments which will be passed to the
    :term:`venusian` ``attach`` function are ``_depth`` and ``_category``.

    ``_depth`` is provided for people who wish to reuse this class from another
    decorator. The default value is ``0`` and should be specified relative to
    the ``view_config`` invocation. It will be passed in to the
    :term:`venusian` ``attach`` function as the depth of the callstack when
    Venusian checks if the decorator is being used in a class or module
    context. It's not often used, but it can be useful in this circumstance.

    ``_category`` sets the decorator category name. It can be useful in
    combination with the ``category`` argument of ``scan`` to control which
    views should be processed.

    See the :py:func:`venusian.attach` function in Venusian for more
    information about the ``_depth`` and ``_category`` arguments.

    .. warning::

        ``resource_view_config`` will work ONLY on module top level members
        because of the limitation of ``venusian.Scanner.scan``.

    """
    venusian = venusian  # for testing injection

    def __init__(self, resource_class: Optional[Type[Resource]] = None, **predicates):
        self.resource_class = resource_class
        self.predicates = predicates
        self.depth = predicates.pop('_depth', 0)
        self.category = predicates.pop('_category', 'restfw')

    def register(self, scanner, name, wrapped):
        config: Configurator = scanner.config
        config.add_resource_view(
            view_class=wrapped,
            resource_class=self.resource_class,
            **self.predicates
        )

    def __call__(self, wrapped):
        if self.resource_class is None:
            hints = get_type_hints(wrapped)
            resource_class = hints.get('resource')
            if resource_class is None:
                raise RuntimeError(
                    'You must specify "resource_class" argument for decorator "resource_view_config" '
                    f'or add type-hint of resource field of class {wrapped.__class__.__name__}.'
                )
            self.resource_class = resource_class
        self.venusian.attach(wrapped, self.register, category=self.category,
                             depth=self.depth + 1)
        return wrapped


@resource_view_config()
@implementer(interfaces.IResourceView)
class ResourceView:
    resource: Resource

    def __init__(self, context: Resource, request: PyramidRequest):
        self.resource = context
        self.request = request

    def __str__(self):
        return f'<{self.__class__.__name__} for {self.resource}>'

    def __repr__(self):
        return str(self)

    def __json__(self) -> Json:
        return self.as_dict()

    def as_dict(self) -> Json:
        return {}

    def http_options(self):
        allowed_methods = ', '.join(self.get_allowed_methods())
        self.request.response.headers['Allow'] = allowed_methods
        if 'Access-Control-Request-Method' in self.request.headers:
            self.request.response.headers['Access-Control-Allow-Methods'] = allowed_methods
        return self.request.response

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.ResourceSchema)

    def http_head(self):
        return self.http_get()

    def http_get(self):
        """Returns a resource representation."""
        self._process_result(result=self.resource, context=self.resource)
        return self.__json__()

    options_for_post: Optional[interfaces.MethodOptions] = None

    def http_post(self):
        params = self._get_params()
        try:
            result, created = self.resource.http_post(self.request, params)
        except ParameterError as e:
            raise create_validation_error(
                self.options_for_post.input_schema,
                message=e.err_message,
                node_name=e.name,
                value=e.value,
            ) from e
        return self._process_result(result, created)

    options_for_put: Optional[interfaces.MethodOptions] = None

    def http_put(self):
        params = self._get_params()
        try:
            created = self.resource.http_put(self.request, params)
        except ParameterError as e:
            raise create_validation_error(
                self.options_for_put.input_schema,
                message=e.err_message,
                node_name=e.name,
                value=e.value,
            ) from e
        self._process_result(result=self.resource, created=created, context=self.resource)
        return self.__json__()

    options_for_patch: Optional[interfaces.MethodOptions] = None

    def http_patch(self):
        params = self._get_params()
        try:
            created = self.resource.http_patch(self.request, params)
        except ParameterError as e:
            raise create_validation_error(
                self.options_for_patch.input_schema,
                message=e.err_message,
                node_name=e.name,
                value=e.value,
            ) from e
        self._process_result(result=self.resource, created=created, context=self.resource)
        return self.__json__()

    options_for_delete: Optional[interfaces.MethodOptions] = None

    def http_delete(self):
        params = self._get_params()
        try:
            result = self.resource.http_delete(self.request, params)
        except ParameterError as e:
            raise create_validation_error(
                self.options_for_delete.input_schema,
                message=e.err_message,
                node_name=e.name,
                value=e.value,
            ) from e
        return self._process_result(result)

    def get_allowed_methods(self) -> Set[str]:
        methods = {'OPTIONS'}
        for method in ('get', 'put', 'patch', 'delete', 'post'):
            method_options = f'options_for_{method}'
            method_options = getattr(self, method_options, None)
            if method_options is not None:
                methods.add(method.upper())
        if 'GET' in methods:
            methods.add('HEAD')
        return methods

    def _get_params(self) -> Union[dict, list]:
        request_method = self.request.method.lower()
        request_method = 'get' if request_method == 'head' else request_method
        method_options: Optional[interfaces.MethodOptions] = getattr(self, f'options_for_{request_method}', None)
        input_schema = method_options.input_schema if method_options else None
        return get_input_data(self.resource, self.request, input_schema) if input_schema else {}

    def _process_result(self, result, created=False, context=None):
        if result is None:
            return httpexceptions.HTTPNoContent()
        if created:
            self.request.response.status = 201
            if ILocation.providedBy(result):
                self.request.response.headers['Location'] = self.request.resource_url(result)
        _try_add_etag(self.request, result, context=context)
        return result


@resource_view_config()
@implementer(interfaces.IHalResourceView)
class HalResourceView(ResourceView):
    resource: HalResource
    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.HalResourceSchema)

    def __json__(self) -> Json:
        result = self.as_dict()
        links = self.get_links()
        registry = self.request.registry

        # Add external links
        for name, link_fabric in get_external_links(self.resource, registry):
            if name in links:
                # Don't overwrite the link added by resource
                continue
            link = link_fabric.get_link(self.request)
            if not link:
                continue
            link = {'href': link}
            if link_fabric.templated:
                link['templated'] = True
            links[name] = link

        # Add links to sub-resources
        self_url = links['self']['href']
        for name, _ in self.resource.get_sub_resources(registry):
            if name in links:
                # Don't overwrite the link added by resource
                continue
            links[name] = {'href': self_url + quote_path_segment(name) + '/'}
        result['_links'] = links
        return result

    def as_embedded(self) -> dict:
        result = self.as_dict()
        # The embedded version of resource has not external links and links to sub-resources
        result['_links'] = self.get_links()
        return result

    def get_links(self) -> dict:
        return {'self': {'href': self.request.resource_url(self.resource)}}


class EmbeddedResources:
    __slots__ = ('paging_links', 'total_count', 'embedded')

    def __init__(self, paging_links=None, total_count=None, **kwargs):
        self.paging_links = paging_links or {}
        self.total_count = total_count
        self.embedded = kwargs

    def __json__(self, request: PyramidRequest):
        result = {}
        for key, resources in self.embedded.items():
            if resources is None:
                continue
            if not isinstance(resources, (dict, str)) and hasattr(resources, '__iter__'):
                rendered = []
                for resource in resources:
                    view = get_resource_view(resource, request)
                    if view:
                        if hasattr(view, 'as_embedded'):
                            rendered.append(view.as_embedded())
                        else:
                            rendered.append(view.__json__())
                    else:
                        rendered.append(resource)
            elif interfaces.IHalResource.providedBy(resources):
                view = get_resource_view(resources, request)
                if view:
                    if hasattr(view, 'as_embedded'):
                        rendered = view.as_embedded()
                    else:
                        rendered = view.__json__()
                else:
                    rendered = resources
            else:
                rendered = resources
            result[key] = rendered
        if self.total_count is not None:
            request.response.headers['X-Total-Count'] = str(self.total_count)
        return result


@implementer(interfaces.IHalResourceWithEmbeddedView)
class HalResourceWithEmbeddedView(HalResourceView):
    options_for_get = interfaces.MethodOptions(
        schemas.GetEmbeddedSchema,
        schemas.HalResourceWithEmbeddedSchema,
    )

    def http_get(self):
        params = self._get_params()
        result = self.__json__()
        if params.get('embedded', True):
            embedded_resources = self.get_embedded(params)
            if embedded_resources:
                result['_embedded'] = embedded_resources
                result['_links'].update(embedded_resources.paging_links)
        return self._process_result(result, context=self.resource)

    def get_embedded(self, params: dict) -> EmbeddedResources:
        return EmbeddedResources(total_count=0, items=[])


def list_to_embedded_resources(request: PyramidRequest, params, resources, parent, embedded_name: str):
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


class _IterLength:

    def __init__(self, iterable):
        self._iterable = iterable
        self._len = 0

    def __iter__(self):
        return self

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
        page.pop(limit)
    paging_links = get_paging_links(parent, request, offset, limit, has_next_page)
    embedded = {embedded_name: page}
    total_count = iterable.get_len() if params['total_count'] else None
    return EmbeddedResources(paging_links, total_count, **embedded)


def _try_add_etag(request: PyramidRequest, result, context: Optional[Resource] = None):
    etag = None
    if interfaces.IResource.providedBy(result):
        etag = result.get_etag()
    elif context is not None:
        etag = context.get_etag()
    if etag is not None:
        request.response.etag = (etag.value, etag.is_strict)


@resource_view_config()
class SimpleContainerView(HalResourceView):
    resource: SimpleContainer

    def get_links(self) -> dict:
        links = super().get_links()
        self_url = links['self']['href']
        for key in self.resource.keys():
            links[key] = {'href': self_url + key + '/'}
        return links
