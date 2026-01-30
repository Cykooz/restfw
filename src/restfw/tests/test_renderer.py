# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 28.08.2020
"""

import pytest
from pyramid import testing
from pyramid.renderers import RendererHelper

from ..renderers import add_adapter_into_json_renderer
from ..utils import open_pyramid_request


def test_unicode():
    with testing.testConfig() as config:
        config.add_renderer(None, 'restfw.renderers.json_renderer')
        config.commit()
        renderer = RendererHelper(registry=config.registry)

        with open_pyramid_request(config.registry) as request:
            data = {'key': 'Значение'}
            res = renderer.render(data, system_values=None, request=request)
            assert res == '{"key": "Значение"}'


class SomeClass:
    def __init__(self, v):
        self.v = v


def some_adapter(value, request):
    return value.v


def test_add_adapter():
    with testing.testConfig() as config:
        config.add_renderer(None, 'restfw.renderers.json_renderer')
        config.commit()
        renderer = RendererHelper(registry=config.registry)

        with open_pyramid_request(config.registry) as request:
            data = SomeClass(10)
            with pytest.raises(TypeError):
                res = renderer.render(data, system_values=None, request=request)

    with testing.testConfig() as config:
        config.add_renderer(None, 'restfw.renderers.json_renderer')
        config.commit()
        renderer = RendererHelper(registry=config.registry)
        add_adapter_into_json_renderer(SomeClass, some_adapter)
        add_adapter_into_json_renderer(SomeClass, some_adapter)  # no errors

        with open_pyramid_request(config.registry) as request:
            data = SomeClass(10)
            res = renderer.render(data, system_values=None, request=request)
            assert res == '10'
