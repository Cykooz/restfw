"""
:Authors: cykooz
:Date: 12.01.2021
"""
import venusian
from pyramid.registry import Registry

from . import interfaces


def get_external_links(resource, registry: Registry):
    for name, fabric in registry.getAdapters((resource,), interfaces.IExternalLinkAdapter):
        yield name, fabric


class external_link_config(object):
    """ A function, class or method :term:`decorator` which allows a
    developer to create fabric of external link registrations nearer to it
    definition than use :term:`imperative configuration` to do the same.

    For example, this code in a module ``resources.py``::

      @external_link_config('current_user', IRoot)
      def current_user_link(request, resource):
          return request.resource_url(request.user)

    Might replace the following call to the
    :meth:`restfw.config.add_external_link_fabric` method::

       from .resources import current_user_link
       config.add_external_link_fabric(current_user_link, name='current_user', parent=IRoot)

    Any ``**predicate`` arguments will be passed along to
    :meth:`restfw.config.add_external_link_fabric`.

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

        ``external_link_config`` will work ONLY on module top level members
        because of the limitation of ``venusian.Scanner.scan``.

    """
    venusian = venusian  # for testing injection

    def __init__(self, name, resource_type=interfaces.IHalResource,
                 title='', description='',
                 optional=False, templated=False, **predicates):
        self.name = name
        self.resource_type = resource_type
        self.title = title
        self.description = description
        self.optional = optional
        self.templated = templated
        self.predicates = predicates
        self.depth = predicates.pop('_depth', 0)
        self.category = predicates.pop('_category', 'pyramid')

    def register(self, scanner, name, wrapped):
        config = scanner.config
        config.add_external_link_fabric(
            wrapped, self.name, self.resource_type,
            title=self.title,
            description=self.description,
            optional=self.optional,
            templated=self.templated,
            **self.predicates
        )

    def __call__(self, wrapped):
        self.venusian.attach(wrapped, self.register, category=self.category,
                             depth=self.depth + 1)
        return wrapped
