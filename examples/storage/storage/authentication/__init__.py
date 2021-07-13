# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2020
"""
from pyramid.config import Configurator


def includeme(config: Configurator):
    from .policy import ExampleSecurityPolicy
    config.set_security_policy(ExampleSecurityPolicy())

    from restfw.utils import scan_ignore
    config.scan(ignore=scan_ignore(config.registry))
