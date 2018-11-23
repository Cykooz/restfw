# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.11.2018
"""
from functools import update_wrapper

import venusian
from zope.interface.verify import verifyObject

from . import interfaces


def _derive_fabric(fabric, predicates):
    """
    :type fabric: interfaces.ISubResourceFabric
    :type predicates: list
    :rtype: interfaces.ISubResourceFabric
    """
    def fabric_wrapper(parent):
        if all((predicate(parent) for predicate in predicates)):
            return fabric(parent)

    if hasattr(fabric, '__name__'):
        update_wrapper(fabric_wrapper, fabric)

    return fabric_wrapper


def add_sub_resource_fabric(config, fabric, name, parent=interfaces.IResource, **predicates):
    """A configurator command for register sub-resource fabric.
    :type config: pyramid.config.Configurator
    :type fabric: interfaces.ISubResourceFabric
    :type name: str
    :type parent: type or zope.interface.Interface
    :type predicates: dict

    Using the default ``parent`` value, ``IResource`` will cause the sub resource
    fabric to be registered for all resource types.

    Any number of predicate keyword arguments may be passed in
    ``**predicates``.  Each predicate named will narrow the set of
    circumstances in which the sub resource fabric will be invoked. Each named
    predicate must have been registered via
    :meth:`restfw.config.add_sub_resource_fabric_predicate` before it
    can be used.
    """

    dotted = config.maybe_dotted
    fabric, parent = dotted(fabric), dotted(parent)
    verifyObject(interfaces.ISubResourceFabric, fabric, tentative=True)

    if not isinstance(parent, (tuple, list)):
        parent = (parent,)

    intr = config.introspectable(
        'sub_resource_fabrics',
        id(fabric),
        config.object_description(fabric),
        'sub_resource_fabric'
    )
    intr['fabric'] = fabric
    intr['parent'] = parent

    def register():
        pred_list = config.get_predlist('sub_resource_fabric')
        order, preds, phash = pred_list.make(config, **predicates)
        derived_fabric = _derive_fabric(fabric, preds)

        intr.update({
            'phash': phash,
            'order': order,
            'predicates': preds,
            'derived_fabric': derived_fabric,
        })

        config.registry.registerAdapter(derived_fabric, required=parent, provided=interfaces.IResource, name=name)

    config.action(None, register, introspectables=(intr,))
    return fabric


def add_sub_resource_fabric_predicate(config, name, factory, weighs_more_than=None,
                                      weighs_less_than=None):
    """
    :type config: pyramid.config.Configurator
    :type name: str
    :param factory:
    :param weighs_more_than:
    :param weighs_less_than:

    Adds a sub resource fabric predicate factory. The associated
    sub resource fabric predicate can later be named as a keyword argument to
    :meth:`pyramid.config.Configurator.add_sub_resource_fabric` in the
    ``**predicates`` anonymous keyword argument dictionary.

    ``name`` should be the name of the predicate.  It must be a valid
    Python identifier (it will be used as a ``**predicates`` keyword
    argument to :meth:`~restfw.config.add_sub_resource_fabric`).

    ``factory`` should be a :term:`predicate factory` or :term:`dotted
    Python name` which refers to a predicate factory.
    """
    config._add_predicate(
        'sub_resource_fabric',
        name,
        factory,
        weighs_more_than=weighs_more_than,
        weighs_less_than=weighs_less_than
    )


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

    def __init__(self, name, parent=interfaces.IResource, **predicates):
        self.name = name
        self.parent = parent
        self.predicates = predicates
        self.depth = predicates.pop('_depth', 0)
        self.category = predicates.pop('_category', 'restfw')

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_sub_resource_fabric(wrapped, self.name, self.parent, **self.predicates)

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category=self.category,
                             depth=self.depth + 1)
        return wrapped
