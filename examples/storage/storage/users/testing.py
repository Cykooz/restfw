# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
from .resources import get_users, User


def create_user(request, name):
    """
    :type request: pyramid.request.Request
    :type name: str
    :rtype: User
    """
    users = get_users(request.root)
    try:
        user = users[name]
    except KeyError:
        user, _ = users.http_post(request, {'name': name})
    return user
