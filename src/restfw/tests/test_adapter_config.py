"""
:Authors: cykooz
:Date: 03.09.2025
"""

import pytest
from zope.interface import Interface, implementer

from ..config.adapters import adapter_config


class IAdapted(Interface):
    def __call__(): ...


class IAdaptable(Interface): ...


@implementer(IAdapted)
class OneArgWoTyping:
    def __init__(self, item):
        self.item = item


@implementer(IAdaptable)
class Adaptable: ...


@implementer(IAdapted)
class TwoArgs:
    def __init__(self, item: str, date):
        self.item = item
        self.date = date


@implementer(IAdapted)
class ThreeArgs:
    def __init__(self, item: str, date: int, flag: bool):
        self.item = item
        self.date = date
        self.flag = flag


class Venusian:
    def __init__(self, config):
        self.config = config
        self.calls = []

    def attach(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def test_one_arg_wo_typing(app_config):
    adapter = OneArgWoTyping
    venusian = Venusian(app_config)

    decorator = adapter_config()
    decorator.venusian = venusian
    with pytest.raises(RuntimeError, match='Not all arguments .* has a type hint'):
        decorator(adapter)

    decorator = adapter_config(required=[str, int])
    decorator.venusian = venusian
    with pytest.raises(RuntimeError, match='does not match the number of'):
        decorator(adapter)

    decorator = adapter_config(required=[str], must_implement=IAdaptable)
    decorator.venusian = venusian
    with pytest.raises(RuntimeError, match='does not implement'):
        decorator(adapter)

    decorator = adapter_config(required=[Adaptable], must_implement=[IAdaptable])
    decorator.venusian = venusian
    decorator(adapter)
    assert decorator.required == [Adaptable]
    assert decorator.provided is None

    decorator = adapter_config(required=[str])
    decorator.venusian = venusian
    decorator(adapter)
    assert decorator.required == [str]
    assert decorator.provided is None

    decorator.register(venusian, '', adapter)


def test_two_args(app_config):
    adapter = TwoArgs
    venusian = Venusian(app_config)

    decorator = adapter_config()
    decorator.venusian = venusian
    with pytest.raises(RuntimeError, match='Not all arguments .* has a type hint'):
        decorator(adapter)

    decorator = adapter_config(required=[bool, int])
    decorator.venusian = venusian
    decorator(adapter)
    assert decorator.required == [bool, int]


def test_three_args(app_config):
    adapter = ThreeArgs
    venusian = Venusian(app_config)

    decorator = adapter_config()
    decorator.venusian = venusian
    decorator(adapter)
    assert decorator.required == [str, int, bool]

    decorator.register(venusian, '', adapter)
