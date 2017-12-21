# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.08.2017
"""
import pytest
from pyramid import testing
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.interfaces import IRequestFactory, IRootFactory
from pyramid.request import Request, apply_request_extensions
from pyramid.scripting import prepare
from pyramid.traversal import DefaultRootFactory

from ..testing.webapp import WebApp


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


@pytest.fixture(name='request')
def request_fixture(app_config):
    app_config.include('restfw')
    registry = app_config.registry
    request_factory = registry.queryUtility(IRequestFactory, default=Request)
    request = request_factory.blank('http://localhost')
    request.registry = registry
    apply_request_extensions(request)
    # create pyramid root
    root_factory = request.registry.queryUtility(IRootFactory, default=DefaultRootFactory)
    root = root_factory(request)  # Initialise pyramid root
    if hasattr(root, 'set_request'):
        root.set_request(request)
    request.root = root
    return request
