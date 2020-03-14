# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
import pytest


@pytest.fixture(name='pyramid_apps')
def pyramid_apps_fixture():
    return [
        'storage.authentication'
    ]
