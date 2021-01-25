"""
:Authors: cykooz
:Date: 13.01.2021
"""
import pytest


@pytest.fixture(name='pyramid_apps')
def pyramid_apps_fixture():
    return [
        'storage.files'
    ]
