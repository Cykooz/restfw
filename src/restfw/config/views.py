"""
:Authors: cykooz
:Date: 12.01.2021
"""

import operator
from typing import Optional, Type

from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.interfaces import IRequest
from pyramid.registry import Deferred
from zope.interface import Interface, implementedBy
from zope.interface.interfaces import IInterface
from zope.interface.verify import verifyClass

from .. import interfaces
from ..interfaces import IResource, IResourceView
from ..typing import PyramidRequest


def _method_not_allowed_view(request: PyramidRequest):
    raise HTTPMethodNotAllowed(
        detail={'method': request.method},
    )


def add_resource_view(config: Configurator, view_class, resource_class, **predicates):
    """A configurator command for register python class as resource view."""
    dotted = config.maybe_dotted
    view_class, resource_class = dotted(view_class), dotted(resource_class)
    verifyClass(interfaces.IResourceView, view_class, tentative=True)

    not_allowed_methods = []
    for http_method in ('get', 'post', 'put', 'patch', 'delete'):
        method_options: Optional[interfaces.MethodOptions] = getattr(
            view_class, f'options_for_{http_method}', None
        )
        if method_options is None:
            not_allowed_methods.append(http_method.upper())
            continue

        permission = (
            f'{http_method}.{method_options.permission}'
            if method_options.permission
            else http_method
        )
        methods = ['head', 'get'] if http_method == 'get' else [http_method]
        for request_method in methods:
            method = request_method.upper()
            config.add_view(
                view=view_class,
                request_method=method,
                context=resource_class,
                permission=permission,
                attr=f'http_{request_method}',
                **predicates,
            )

    if not_allowed_methods:
        config.add_view(
            view=_method_not_allowed_view,
            request_method=not_allowed_methods,
            context=resource_class,
            **predicates,
        )

    config.add_view(
        view=view_class,
        request_method='OPTIONS',
        context=resource_class,
        attr='http_options',
        **predicates,
    )

    _register_resource_view(
        config,
        view_class,
        resource_class,
        **predicates,
    )


def _register_resource_view(
    config: Configurator,
    view_class: Type[IResourceView],
    resource_class: Type[IResource],
    request_type=None,
    containment=None,
    name='',
    **view_options,
):
    view_class = config.maybe_dotted(view_class)
    resource_class = config.maybe_dotted(resource_class)
    containment = config.maybe_dotted(containment)

    if not view_class:
        raise ConfigurationError('"view_class" was not specified')

    if request_type is not None:
        request_type = config.maybe_dotted(request_type)
        if not IInterface.providedBy(request_type):
            raise ConfigurationError(
                'request_type must be an interface, not %s' % request_type
            )

    introspectables = []
    ovals = view_options.copy()
    ovals.update(
        dict(
            containment=containment,
            request_type=request_type,
        )
    )

    r_resource_class = resource_class
    if r_resource_class is None:
        r_resource_class = Interface
    if not IInterface.providedBy(r_resource_class):
        r_resource_class = implementedBy(r_resource_class)

    def discrim_func():
        # We need to defer the discriminator until we know what the phash
        # is. It can't be computed any sooner because third-party
        # predicates/view derivers may not yet exist when add_view is
        # called.
        predlist = config.get_predlist('view')
        valid_predicates = predlist.names()
        pvals = {}

        for k, v in ovals.items():
            if k in valid_predicates:
                pvals[k] = v

        order, preds, phash = predlist.make(config, **pvals)

        view_intr.update({'phash': phash, 'order': order, 'predicates': preds})
        return 'serializer', resource_class, phash

    discriminator = Deferred(discrim_func)

    view_intr = config.introspectable(
        category_name='Resource views',
        discriminator=discriminator,
        title=config.object_description(view_class),
        type_name='resource view',
    )
    view_intr.update(
        dict(
            name=name,
            context=resource_class,
            containment=containment,
            callable=view_class,
        )
    )
    view_intr.update(view_options)
    introspectables.append(view_intr)

    def register():
        # __discriminator__ is used by super-dynamic systems
        # that require it for introspection after manual view lookup;
        # see also MultiResourceView.__discriminator__
        view_class.__discriminator__ = lambda *arg: discriminator

        # A resource_views is a set of views which are registered for
        # exactly the same resource type/request type/name triad. Each
        # constituent view in a resource_views differs only by the
        # predicates which it possesses.

        # To find a previously registered view for a resource
        # type/request type/name triad, we need to use the
        # ``registered`` method of the adapter registry rather than
        # ``lookup``. ``registered`` ignores interface inheritance
        # for the required and provided arguments, returning only a
        # view registered previously with the *exact* triad we pass
        # in.

        request_iface = IRequest
        registered = config.registry.adapters.registered
        multi_resource_views = registered(
            (request_iface, r_resource_class), IResourceView, name
        )

        if not multi_resource_views:
            multi_resource_views = MultiResourceView(name)
            config.registry.registerAdapter(
                multi_resource_views,
                (request_iface, resource_class),
                IResourceView,
                name,
            )

        multi_resource_views.add(
            view_class,
            view_intr['order'],
            view_intr['phash'],
            view_intr['predicates'],
        )

    config.action(discriminator, register, introspectables=introspectables)


class MultiResourceView:
    __slots__ = ('name', 'views')

    def __init__(self, name):
        self.name = name
        self.views = []

    def __discriminator__(self, context, request: PyramidRequest):
        # used by introspection systems like so:
        # view = adapters.lookup(....)
        # view.__discriminator__(context, request) -> view's discriminator
        # so that superdynamic systems can feed the discriminator to
        # the introspection system to get info about it
        view = self.get_view_class(request, context)
        return view.__discriminator__(context, request)

    def add(self, view, order, phash=None, predicates=None):
        if phash is not None:
            for i, (_, _, h, _) in enumerate(list(self.views)):
                if phash == h:
                    self.views[i] = (order, view, phash, predicates)
                    return
        self.views.append((order, view, phash, predicates))
        self.views.sort(key=operator.itemgetter(0))

    def get_view_class(
        self, request: PyramidRequest, resource: IResource
    ) -> Optional[Type[IResourceView]]:
        for order, view, phash, predicates in self.views:
            if not predicates:
                return view
            if all(predicate(resource, request) for predicate in predicates):
                return view

    def __call__(
        self, request: PyramidRequest, resource: IResource
    ) -> Optional[IResourceView]:
        view_class = self.get_view_class(request, resource)
        if view_class:
            return view_class(resource, request)
