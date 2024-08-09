# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""

from functools import update_wrapper

import venusian
from zope.interface.verify import verifyObject

from . import interfaces
from ..utils import get_object_fullname


def _derive_usage_examples_fabric(fabric, predicates):
    """
    :type fabric: interfaces.IUsageExamplesFabric
    :type predicates: list
    :rtype: interfaces.IUsageExamplesFabric
    """

    def fabric_wrapper(request):
        if all((predicate(request) for predicate in predicates)):
            return fabric(request)

    if hasattr(fabric, '__name__'):
        update_wrapper(fabric_wrapper, fabric)

    return fabric_wrapper


def add_usage_examples_fabric(config, fabric, name='', **predicates):
    """A configurator command for register fabric of resource usage examples.
    :type config: pyramid.config.Configurator
    :type fabric: interfaces.IUsageExamplesFabric
    :type name: str
    :type predicates: dict

    Any number of predicate keyword arguments may be passed in
    ``**predicates``. Each predicate named will narrow the set of
    circumstances in which the examples fabric will be invoked. Each named
    predicate must have been registered via
    :meth:`restfw.usage_examples.config.add_usage_examples_fabric_predicate` before it
    can be used.
    """

    dotted = config.maybe_dotted
    fabric = dotted(fabric)
    verifyObject(interfaces.IUsageExamplesFabric, fabric, tentative=True)
    if not name:
        name = get_object_fullname(fabric)

    intr = config.introspectable(
        'usage_examples_fabrics',
        id(fabric),
        config.object_description(fabric),
        'usage_examples_fabric',
    )
    intr['fabric'] = fabric

    def register():
        pred_list = config.get_predlist('usage_examples_fabric')
        order, preds, phash = pred_list.make(config, **predicates)
        derived_fabric = _derive_usage_examples_fabric(fabric, preds)

        intr.update(
            {
                'phash': phash,
                'order': order,
                'predicates': preds,
                'derived_fabric': derived_fabric,
            }
        )

        config.registry.registerUtility(
            derived_fabric, provided=interfaces.IUsageExamplesFabric, name=name
        )

    config.action(None, register, introspectables=(intr,))
    return fabric


def add_usage_examples_fabric_predicate(
    config, name, factory, weighs_more_than=None, weighs_less_than=None
):
    """
    :type config: pyramid.config.Configurator
    :type name: str
    :param factory:
    :param weighs_more_than:
    :param weighs_less_than:

    Adds a resource usage examples fabric predicate factory. The associated
    resource examples fabric predicate can later be named as a keyword argument to
    :meth:`pyramid.config.Configurator.add_usage_examples_fabric` in the
    ``**predicates`` anonymous keyword argument dictionary.

    ``name`` should be the name of the predicate. It must be a valid
    Python identifier (it will be used as a ``**predicates`` keyword
    argument to :meth:`~restfw.usage_examples.config.add_usage_examples_fabric`).

    ``factory`` should be a :term:`predicate factory` or :term:`dotted
    Python name` which refers to a predicate factory.
    """
    config._add_predicate(
        'usage_examples_fabric',
        name,
        factory,
        weighs_more_than=weighs_more_than,
        weighs_less_than=weighs_less_than,
    )


class examples_config(object):
    """A function, class or method :term:`decorator` which allows a
    developer to create resource usage examples fabric registrations nearer to it
    definition than use :term:`imperative configuration` to do the same.

    For example, this code in a module ``examples.py``::

        @examples_config()
        class UsersExamples(UsageExamples):

            def prepare_resource(self):
                create_user_with_token('user')
                create_user_with_token('admin', role='admin')
                return self.root['users']

    Might replace the following call to the
    :meth:`restfw.usage_examples.config.add_usage_examples_fabric` method::

       from .examples import UsersExamples
       config.add_usage_examples_fabric(UsersExamples)

    Any ``**predicate`` arguments will be passed along to
    :meth:`restfw.usage_examples.config.add_usage_examples_fabric`.

    Two additional keyword arguments which will be passed to the
    :term:`venusian` ``attach`` function are ``_depth`` and ``_category``.

    ``_depth`` is provided for people who wish to reuse this class from another
    decorator. The default value is ``0`` and should be specified relative to
    the ``examples_config`` invocation. It will be passed in to the
    :term:`venusian` ``attach`` function as the depth of the callstack when
    Venusian checks if the decorator is being used in a class or module
    context. It's not often used, but it can be useful in this circumstance.

    ``_category`` sets the decorator category name. It can be useful in
    combination with the ``category`` argument of ``scan`` to control which
    resource examples fabric should be processed.

    See the :py:func:`venusian.attach` function in Venusian for more
    information about the ``_depth`` and ``_category`` arguments.

    .. warning::

        ``examples_config`` will work ONLY on module top level members
        because of the limitation of ``venusian.Scanner.scan``.
    """

    venusian = venusian  # for testing injection

    def __init__(self, name='', **predicates):
        self.name = name
        self.predicates = predicates
        self.depth = predicates.pop('_depth', 0)
        self.category = predicates.pop('_category', 'pyramid')

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_usage_examples_fabric(wrapped, self.name, **self.predicates)

    def __call__(self, wrapped):
        self.venusian.attach(
            wrapped, self.register, category=self.category, depth=self.depth + 1
        )
        return wrapped
