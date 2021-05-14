# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
from restfw.typing import PyramidRequest
from .resources import get_users, User


def create_user(request: PyramidRequest, name: str) -> User:
    users = get_users(request.root)
    try:
        user = users[name]
    except KeyError:
        user, _ = users.http_post(request, {'name': name})
    return user
