# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.01.2020
"""


def includeme(config):
    """
    :type config: pyramid.config.Configurator
    """
    config.include('restfw')
    config.include('storage.authentication')

    from restfw.interfaces import IRootCreated
    from .resources import Users

    def add_to_root(event):
        event.root['users'] = Users()

    config.add_subscriber(add_to_root, IRootCreated)

    from restfw.utils import scan_ignore
    config.scan(ignore=scan_ignore(config.registry))
