# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
import warnings

try:
    import pytest
    pytest.register_assert_rewrite(
        'restfw.testing.resource_testing',
        'restfw.testing.webapp',
    )
except (ImportError, AttributeError):
    pass

from .resource_testing import assert_resource
from .. import utils


def get_pyramid_root(request=None):
    warnings.warn(
        'Function restfw.testing:get_pyramid_root will be removed at next major release. '
        'Please use it new version restfw.utils:get_pyramid_root',
        stacklevel=2
    )
    return utils.get_pyramid_root(request)


def open_pyramid_request(app_config):
    """
    :type app_config: pyramid.config.Configurator
    :rtype: pyramid.request.Request
    """
    warnings.warn(
        'Function restfw.testing:open_pyramid_request will be removed at the next major release. '
        'Please use it new version restfw.utils:open_pyramid_request',
        stacklevel=2
    )
    return utils.open_pyramid_request(app_config.registry)
