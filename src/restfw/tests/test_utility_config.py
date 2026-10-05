"""
:Authors: cykooz
:Date: 02.10.2026
"""

import pytest
from zope.interface import Interface

from ..config.utilities import utility_config


class IUtility1(Interface):
    def __call__(arg: str): ...


def utility1_impl1(arg: str):
    pass


def not_utility1_impl(foo: int, bar: str):
    pass


class NotUtility1Impl:
    def __call__(self, foo: int, bar: str):
        pass


class Utility1Impl2:
    def __call__(self, arg: str):
        pass


class IUtility2(Interface):
    def run(arg: str):
        pass


class Utility2Impl:
    def run(self, arg: str):
        pass


class Venusian:
    def __init__(self, config):
        self.config = config
        self.calls = []

    def attach(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def test_utility_config(app_config):
    venusian = Venusian(app_config)

    decorator = utility_config(IUtility1)
    decorator.venusian = venusian
    decorator(utility1_impl1)

    # zope.interface.verify.verifyObject cannot check functions
    decorator(not_utility1_impl)
    # But it can check objects
    with pytest.raises(RuntimeError, match='does not provide'):
        decorator(NotUtility1Impl())

    decorator = utility_config(
        IUtility1,
    )
    decorator.venusian = venusian
    decorator(Utility1Impl2())

    decorator = utility_config(IUtility2)
    decorator.venusian = venusian
    decorator(Utility2Impl())
