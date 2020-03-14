# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2020
"""


def includeme(config):
    """
    :type config: pyramid.config.Configurator
    """
    from pyramid.authentication import BasicAuthAuthenticationPolicy
    from .models import get_user_principals

    auth_policy = BasicAuthAuthenticationPolicy(get_user_principals, realm='Storage Example')
    config.set_authentication_policy(auth_policy)

    from restfw.utils import scan_ignore
    config.scan(ignore=scan_ignore(config.registry))
