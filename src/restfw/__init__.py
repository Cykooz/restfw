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
    from . import predicates
    from .viewderivers import register_view_derivers

    config.set_authorization_policy(RestACLAuthorizationPolicy())
    config.set_root_factory('restfw.root.root_factory')
    config.add_renderer(None, 'restfw.renderers.json_renderer')
    predicates = [
        ('debug', predicates.DebugPredicate),
        ('testing', predicates.TestingPredicate),
        ('debug_or_testing', predicates.DebugOrTestingPredicate),
    ]
    for name, fabric in predicates:
        config.add_view_predicate(name, fabric)
        config.add_subscriber_predicate(name, fabric)

    from .config import add_sub_resource_fabric, add_sub_resource_fabric_predicate
    config.add_directive('add_sub_resource_fabric', add_sub_resource_fabric)
    config.add_directive('add_sub_resource_fabric_predicate', add_sub_resource_fabric_predicate)

    from .config import add_external_link_fabric, add_external_link_fabric_predicate
    config.add_directive('add_external_link_fabric', add_external_link_fabric)
    config.add_directive('add_external_link_fabric_predicate', add_external_link_fabric_predicate)

    from .usage_examples.config import add_usage_examples_fabric_predicate
    from .usage_examples.config import add_usage_examples_fabric
    config.add_directive('add_usage_examples_fabric', add_usage_examples_fabric)
    config.add_directive('add_usage_examples_fabric_predicate', add_usage_examples_fabric_predicate)

    register_view_derivers(config)

    # Fix memory leaks on pyramid segment cache
    import pyramid.traversal
    if pyramid.traversal._segment_cache.__class__ is dict:
        from lru import LRU
        pyramid.traversal._segment_cache = LRU(1000)

    from .utils import scan_ignore
    ignore = scan_ignore(config.registry)
    ignore.extend([
        '.docs_gen',
    ])
    config.scan(ignore=ignore)
