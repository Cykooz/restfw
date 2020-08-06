# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.04.2020
"""
from functools import partial

import pytest
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.scripting import prepare
from pyramid.settings import aslist

from .webapp import WebApp
from ..utils import open_pyramid_request


def simple_app(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    with Configurator(settings=settings) as config:
        auth_policy = BasicAuthAuthenticationPolicy(
            check=lambda username, password, request: username
        )
        config.set_authentication_policy(auth_policy)

        apps = global_config.get('apps', '')
        if not isinstance(apps, (list, tuple)):
            apps = aslist(apps)
        for app in apps:
            config.include(app)

        return config.make_wsgi_app()


def create_app_env(apps=None, pyramid_settings=None):
    global_config = {
        'apps': '\n'.join(apps or []),
    }
    settings = pyramid_settings or {}
    settings['testing'] = True
    wsgi_app = simple_app(global_config, **settings)
    env = prepare()
    env['app'] = wsgi_app
    return env


@pytest.fixture(name='pyramid_apps', scope='session')
def pyramid_apps_fixture():
    return []


@pytest.fixture(name='pyramid_settings', scope='session')
def pyramid_settings_fixture():
    return {}


@pytest.fixture(name='web_app')
def web_app_fixture(pyramid_apps, pyramid_settings):
    """
    :rtype: WebApp
    """
    app_env_fabric = partial(create_app_env, apps=pyramid_apps, pyramid_settings=pyramid_settings)
    with WebApp(app_env_fabric) as web_app:
        yield web_app


@pytest.fixture(name='pyramid_request')
def pyramid_request_fixture(web_app):
    with open_pyramid_request(web_app.registry) as request:
        yield request


@pytest.fixture(name='app_config')
def app_config_fixture(web_app):
    return Configurator(registry=web_app.registry)
