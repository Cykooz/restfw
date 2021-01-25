"""
:Authors: cykooz
:Date: 12.01.2021
"""
from pyramid.config import Configurator


def includeme(config: Configurator):
    from .external_links import add_external_link_fabric, add_external_link_fabric_predicate
    from .sub_resources import add_sub_resource_fabric, add_sub_resource_fabric_predicate
    from .views import add_resource_view

    config.add_directive('add_sub_resource_fabric', add_sub_resource_fabric)
    config.add_directive('add_sub_resource_fabric_predicate', add_sub_resource_fabric_predicate)

    config.add_directive('add_external_link_fabric', add_external_link_fabric)
    config.add_directive('add_external_link_fabric_predicate', add_external_link_fabric_predicate)

    config.add_directive('add_resource_view', add_resource_view)
