# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.08.2017
"""
import pytest
from pyramid import testing
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.request import Request
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
    settings = {
        'zodbconn.uri': 'memory://',
        'testing': True
    }
    wsgi_app = simple_app({}, **settings)
    env = prepare()
    env['app'] = wsgi_app
    return env


@pytest.fixture(name='web_app', scope='module')
def web_app_fixture():
    with WebApp(create_app_env) as web_app:
        yield web_app


@pytest.fixture(name='app_config')
def app_config_fixture():
    settings = {
        'zodbconn.uri': 'memory://'
    }
    request = Request.blank('http://localhost')
    with testing.testConfig(request=request, settings=settings) as config:
        request.registry = config.registry
        yield config
        request._process_finished_callbacks()


@pytest.fixture(name='pyramid_request')
def pyramid_request_fixture(app_config):
    app_config.include('restfw')
    with open_pyramid_request(app_config.registry) as request:
        yield request
