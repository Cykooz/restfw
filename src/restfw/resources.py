# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 19.08.2016
"""
from inspect import isclass
from typing import Generator, Optional, Tuple, Type, get_type_hints

import venusian
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.registry import Registry
from pyramid.traversal import find_root
from zope.interface import implementer

from . import interfaces
from .utils import ETag


@implementer(interfaces.IResource)
class Resource:
    __parent__ = None
    __name__ = None

    def __str__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.__name__)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        if not key:
            raise KeyError(key)
        resource = None
        registry = self.get_registry()
        key = str(key)
        if registry is not None:
            try:
                resource = registry.queryAdapter(self, interfaces.IResource, name=key)
            except KeyError:
                pass
        if not resource:
            raise KeyError(key)
        resource.__name__ = key
        resource.__parent__ = self
        return resource

    def get_sub_resources(self, registry: Registry) -> Generator[Tuple[str, interfaces.IResource], None, None]:
        for name, sub_resource in registry.getAdapters((self,), interfaces.IResource):
            yield name, sub_resource

    @property
    def __resource_name__(self):
        return self.__class__.__name__

    def get_registry(self) -> Registry:
        root = find_root(self)
        return root.registry

    def get_etag(self) -> Optional[ETag]:
        """Returns value of ETag header for the resource or None."""
        return None

    def http_post(self, request, params):
        """Returns a new or modified resource, and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'POST'})

    def http_put(self, request, params):
        """Returns a new or modified resource, and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PUT'})

    def http_patch(self, request, params):
        """Returns a new or modified resource, and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PATCH'})

    def http_delete(self, request, params):
        """Delete the resource."""
        raise HTTPMethodNotAllowed(detail={'method': 'DELETE'})


class sub_resource_config:
    """ A function, class or method :term:`decorator` which allows a
    developer to create sub-resource fabric registrations nearer to it
    definition than use :term:`imperative configuration` to do the same.

    For example, this code in a module ``resources.py``::

      @sub_resource_config('classes', parent=IUser)
      class UserClasses(Resource):

        def __init__(self, parent):
            self.__parent__ = parent


      @sub_resource_config('rooms')
      class UserRooms(Resource):
        __parent__: IUser

        def __init__(self, parent):
            self.__parent__ = parent


      @sub_resource_config('logins')
      def get_user_logins(parent: IUser):
        return UserLogins(parent)

    Might replace the following call to the
    :meth:`restfw.config.add_sub_resource_fabric` method::

       from .resources import UserClasses
       config.add_sub_resource_fabric(UserClasses, name='classes', parent=IUser)

    Any ``**predicate`` arguments will be passed along to
    :meth:`restfw.config.add_sub_resource_fabric`.

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

        ``sub_resource`` will work ONLY on module top level members
        because of the limitation of ``venusian.Scanner.scan``.

    """
    venusian = venusian  # for testing injection

    def __init__(
            self,
            name: str,
            parent: Optional[Type[Resource]] = None,
            add_link_into_embedded=False,
            **predicates
    ):
        self.name = name
        self.parent = parent
        self.add_link_into_embedded = add_link_into_embedded
        self.predicates = predicates
        self.depth = predicates.pop('_depth', 0)
        self.category = predicates.pop('_category', 'pyramid')

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_sub_resource_fabric(
            wrapped,
            self.name,
            self.parent,
            self.add_link_into_embedded,
            **self.predicates
        )

    def __call__(self, wrapped):
        if self.parent is None:
            hints = get_type_hints(wrapped)
            is_class = isclass(wrapped)
            if is_class:
                parent = hints.get('__parent__')
                if parent is None:
                    hints = get_type_hints(wrapped.__init__)
                    parent = hints.get('parent')
            else:
                parent = hints.get('parent')

            if parent is None:
                if is_class:
                    suffix = f'of "__parent__" field of class "{wrapped.__class__.__name__}"'
                else:
                    suffix = f'of "parent" argument of function "{wrapped.__name__}"'
                raise RuntimeError(
                    'You must specify "parent" argument of the decorator "sub_resource_config" '
                    f'or add type-hint {suffix}.'
                )
            self.parent = parent
        self.venusian.attach(wrapped, self.register, category=self.category,
                             depth=self.depth + 1)
        return wrapped
