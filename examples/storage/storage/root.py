# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""

from pyramid.authorization import ALL_PERMISSIONS, Allow, DENY_ALL, Everyone

from restfw.root import Root


class StorageRoot(Root):
    __acl__ = [
        (Allow, Everyone, 'root.get'),
        (Allow, 'admin', ALL_PERMISSIONS),
        # Deny all other permissions for all principals
        DENY_ALL,
    ]
