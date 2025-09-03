"""
:Authors: cykooz
:Date: 03.09.2025
"""

from inspect import Parameter, isclass, signature
from typing import Iterable, Type, TypeVar

import venusian
from pyramid.config import Configurator
from zope.interface import Interface

T = TypeVar('T')


def _into_list(value: Iterable[T] | T | None) -> list[T] | None:
    if value is None:
        return None
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return [value]


class adapter_config:
    venusian = venusian  # for testing

    def __init__(
        self,
        required: Iterable[Type] | Type | None = None,
        provided: Type | None = None,
        must_implement: Iterable[Type[Interface]] | Type[Interface] | None = None,
        name='',
        **kwargs,
    ):
        self.required = _into_list(required)
        self.provided = provided
        self.must_implement: list[Type[Interface]] = _into_list(must_implement) or []
        self.name = name
        self.depth = kwargs.pop('_depth', 0)
        self.category = kwargs.pop('_category', 'pyramid')

    def register(self, scanner, name, wrapped):
        config: Configurator = scanner.config
        config.registry.registerAdapter(
            wrapped,
            self.required,
            self.provided,
            self.name,
        )

    def __call__(self, wrapped):
        wrapper_name = wrapped.__name__
        is_class = isclass(wrapped)
        if is_class:
            func = wrapped.__init__
        else:
            func = wrapped
        func_sign = signature(func, eval_str=True)
        argument_types = []
        required_argument_types = []
        for name, parameter in func_sign.parameters.items():
            if is_class and name == 'self':
                continue
            argument_types.append(parameter.annotation)
            if parameter.default is Parameter.empty:
                required_argument_types.append(parameter.annotation)

        if not argument_types:
            raise RuntimeError(
                f'You must specify at least one argument for the adapter fabric "{wrapper_name}"'
            )
        if self.required and not (
            len(argument_types) >= len(self.required) >= len(required_argument_types)
        ):
            raise RuntimeError(
                'The number of types specified in "required" argument of decorator'
                ' "adapter_config" does not match the number of'
                f' the adapter fabric "{wrapper_name}" arguments.'
            )

        if not self.required:
            if len(argument_types) != len(required_argument_types):
                raise RuntimeError(
                    'You must specify "required" argument of decorator'
                    f' "adapter_config" if the adapter fabric "{wrapper_name}"'
                    ' has arguments with default value.'
                )
            if any(t is Parameter.empty for t in required_argument_types):
                raise RuntimeError(
                    'Not all arguments of the adapter fabric "{wrapper_name}"'
                    ' has a type hint.'
                )
            self.required = required_argument_types

        if self.must_implement:
            for interface, klass in zip(self.must_implement, self.required):
                if not interface.implementedBy(klass):
                    raise RuntimeError(
                        f'"{klass.__name__}" does not implement {interface.__name__}.'
                        ' It is required by argument "must_implement" of decorator'
                        ' "adapter_config" that is used for'
                        f' the adapter fabric "{wrapper_name}".'
                    )

        self.venusian.attach(
            wrapped, self.register, category=self.category, depth=self.depth + 1
        )
        return wrapped
