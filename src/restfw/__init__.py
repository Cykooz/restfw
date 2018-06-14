# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 03.08.2017
"""


def includeme(config):
    """
    :type config: pyramid.config.Configurator
    """
    from .authorization import RestACLAuthorizationPolicy
    from .predicates import DebugPredicate, DebugOrTestingPredicate, TestingPredicate
    from .viewderivers import register_view_derivers

    config.include('pyramid_jinja2')

    config.set_authorization_policy(RestACLAuthorizationPolicy())
    config.set_root_factory('restfw.root.root_factory')
    config.add_renderer(None, 'restfw.renderers.json_renderer')
    config.add_view_predicate('debug', DebugPredicate)
    config.add_view_predicate('debug_or_testing', DebugOrTestingPredicate)
    config.add_view_predicate('testing', TestingPredicate)

    from .resources import add_sub_resource_fabric
    config.add_directive('add_sub_resource_fabric', add_sub_resource_fabric)

    register_view_derivers(config)

    from .utils import scan_ignore
    config.scan(ignore=scan_ignore(config.registry))
