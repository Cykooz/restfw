"""
:Authors: cykooz
:Date: 02.10.2026
"""

import venusian
from pyramid.config import Configurator
from pyramid.registry import Registry
from zope.interface.exceptions import BrokenMethodImplementation
from zope.interface.verify import verifyObject


class utility_config:
    venusian = venusian  # for testing

    def __init__(
        self,
        provided: type | None = None,
        name='',
        **kwargs,
    ):
        self.provided = provided
        self.name = name
        self.depth = kwargs.pop('_depth', 0)
        self.category = kwargs.pop('_category', 'pyramid')

    def register(self, scanner, name, wrapped):
        config: Configurator = scanner.config
        config.registry.registerUtility(
            wrapped,
            self.provided,
            self.name,
        )

    def __call__(self, wrapped):
        if self.provided:
            try:
                verifyObject(self.provided, wrapped, tentative=True)
            except BrokenMethodImplementation:
                raise RuntimeError(
                    f'"{wrapped.__class__.__name__}" does not provide {self.provided.__name__}.'
                )

        self.venusian.attach(
            wrapped, self.register, category=self.category, depth=self.depth + 1
        )
        return wrapped


def get_utilities(registry: Registry, provided: type):
    return registry.getUtilitiesFor(provided)
