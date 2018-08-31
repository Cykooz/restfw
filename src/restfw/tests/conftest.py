# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.08.2017
"""
import pytest
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.scripting import prepare

from ..testing.webapp import WebApp
from ..utils import open_pyramid_request


def simple_app(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    config = Configurator(settings=settings)
    config.include('restfw')
    auth_policy = BasicAuthAuthenticationPolicy(check=lambda username, password, request: username)
    config.set_authentication_policy(auth_policy)
    return config.make_wsgi_app()


def create_app_env():
    settings = {'testing': True}
    wsgi_app = simple_app({}, **settings)
    env = prepare()
    env['app'] = wsgi_app
    return env


@pytest.fixture(name='web_app')
def web_app_fixture():
    with WebApp(create_app_env) as web_app:
        yield web_app


@pytest.fixture(name='pyramid_request')
def pyramid_request_fixture(web_app):
    with open_pyramid_request(web_app.registry) as request:
        yield request


@pytest.fixture(name='app_config')
def app_config_fixture(web_app):
    return Configurator(registry=web_app.registry)
