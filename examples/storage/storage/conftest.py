# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
import shutil
from functools import partial
from tempfile import mkdtemp

import pytest
from pyramid.config import Configurator
from pyramid.scripting import prepare

from restfw.testing.webapp import WebApp
from restfw.utils import open_pyramid_request
from .main import main


@pytest.fixture(name='pyramid_apps', scope='session')
def pyramid_apps_fixture():
    return []


@pytest.fixture(name='data_root')
def data_root_fixture():
    path = mkdtemp()
    yield path
    shutil.rmtree(path, ignore_errors=True)


# Web App

def _create_app_env(data_root, apps=None):
    settings = {
        'testing': True,
        'storage.data_root': data_root,
    }
    if apps:
        settings['pyramid.includes'] = apps
    wsgi_app = main({}, **settings)
    env = prepare()
    env['app'] = wsgi_app
    return env


@pytest.fixture(name='web_app')
def web_app_fixture(pyramid_apps, data_root):
    """
    :rtype: WebApp
    """
    app_env_fabric = partial(_create_app_env, data_root=data_root, apps=pyramid_apps)
    with WebApp(app_env_fabric) as web_app:
        yield web_app


# Pyramid request

@pytest.fixture(name='pyramid_request')
def pyramid_request_fixture(web_app):
    """
    :type web_app: WebApp
    :rtype: pyramid.request.Request
    """
    with open_pyramid_request(web_app.registry) as request:
        yield request


@pytest.fixture(name='app_config')
def app_config_fixture(pyramid_request):
    return Configurator(pyramid_request.registry, autocommit=True)
