# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""


def includeme(config):
    """
    :type config: pyramid.config.Configurator
    """
    config.include('restfw')
    config.include('storage.users')

    from restfw.utils import scan_ignore
    config.scan(ignore=scan_ignore(config.registry))
