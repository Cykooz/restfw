# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.08.2017
"""

import pytest


pytest_plugins = [
    'restfw.testing.fixtures',
]


@pytest.fixture(name='pyramid_apps', scope='session')
def pyramid_apps_fixture():
    return [
        'restfw',
    ]
