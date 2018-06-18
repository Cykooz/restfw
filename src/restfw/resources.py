# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 19.08.2016
"""
import venusian
from pyramid.httpexceptions import HTTPMethodNotAllowed
from pyramid.traversal import find_root
from zope.interface import implementer
from zope.interface.verify import verifyObject

from . import interfaces, schemas


@implementer(interfaces.IResource)
class Resource(object):
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
        request = self.get_request()
        if request:
            try:
                resource = request.registry.queryAdapter(self, interfaces.IResource, name=key)
            except KeyError:
                pass
        if not resource:
            raise KeyError(key)
        resource.__name__ = key
        resource.__parent__ = self
        return resource

    def as_dict(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        return {}

    def __json__(self, request):
        """
        :type request: pyramid.request.Request
        :rtype: dict
        """
        return self.as_dict(request)

    @property
    def __resource_name__(self):
        return self.__class__.__name__

    def get_allowed_methods(self):
        # type: () -> set
        methods = {'OPTIONS'}
        for method in ('get', 'put', 'patch', 'delete', 'post'):
            method_options = 'options_for_%s' % method
            method_options = getattr(self, method_options, None)
            if method_options is not None:
                methods.add(method.upper())
        if 'GET' in methods:
            methods.add('HEAD')
        return methods

    def get_request(self):
        """
        :rtype: pyramid.request.Request
        """
        root = find_root(self)
        return root.request

    options_for_get = interfaces.MethodOptions(schemas.GetResourceSchema, schemas.ResourceSchema)

    def http_head(self, request, params):
        """This method may be used in derived classes to overwrite
        a default implementation for HEAD request handler.
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: IResource
        """
        return self.http_get(request, params)

    def http_get(self, request, params):
        """Returns a resource, any of it representation or any response instance."""
        return self

    options_for_post = None

    def http_post(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'POST'})

    options_for_put = None

    def http_put(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PUT'})

    options_for_patch = None

    def http_patch(self, request, params):
        """Returns a new or modified resource and a flag indicating that the
           resource was created or not."""
        raise HTTPMethodNotAllowed(detail={'method': 'PATCH'})

    options_for_delete = None

    def http_delete(self, request, params):
        """Delete the resource."""
        raise HTTPMethodNotAllowed(detail={'method': 'DELETE'})


def add_sub_resource_fabric(config, fabric, name, parent=interfaces.IResource):
    """A configurator command for register sub-resource fabric.
    :type config: pyramid.config.Configurator
    :type fabric: interfaces.ISubResourceFabric
    :type name: str
    :type parent: type or zope.interface.Interface
    """
    verifyObject(interfaces.ISubResourceFabric, fabric, tentative=True)
    config.registry.registerAdapter(fabric, required=[parent], provided=interfaces.IResource, name=name)


class sub_resource_config(object):
    """ A function, class or method :term:`decorator` which allows a
    developer to create sub-resource fabric registrations nearer to it
    definition than use :term:`imperative configuration` to do the same.

    For example, this code in a module ``resources.py``::

      @sub_resource_config(name='classes', parent=IUser)
      class UserClasses(Resource):

        def __init__(self, parent):
            self.__parent__ = parent

    Might replace the following call to the
    :meth:`pyramid.config.Configurator.add_sub_resource_fabric` method::

       from .resources import UserClasses
       config.add_sub_resource_fabric(UserClasses, name='classes', parent=IUser)

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

    def __init__(self, name, parent=interfaces.IResource, _depth=0, _category='restfw'):
        self.depth = _depth
        self.category = _category
        self.name = name
        self.parent = parent

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_sub_resource_fabric(wrapped, self.name, self.parent)

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category=self.category,
                             depth=self.depth + 1)
        return wrapped
