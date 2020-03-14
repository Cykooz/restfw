# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""
from pyramid.security import Allow, Everyone, DENY_ALL, ALL_PERMISSIONS

from restfw.interfaces import MethodOptions
from restfw.root import Root


class StorageRoot(Root):

    __acl__ = [
        (Allow, Everyone, 'root.get'),
        (Allow, 'admin', ALL_PERMISSIONS),
        # Deny all other permissions for all principals
        DENY_ALL
    ]

    options_for_get = MethodOptions(None, None, 'root.get')
