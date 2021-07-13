# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.01.2020
"""
from pathlib import Path
from typing import Optional

from pyramid.registry import Registry

from ..main import get_data_root


class UserModel(object):

    def __init__(self, name, path):
        """
        :type name: str
        :type path: Path
        """
        self.name = name
        self.path = path

    @classmethod
    def get_model(cls, registry: Registry, name: str) -> Optional['UserModel']:
        data_root = get_data_root(registry)
        path = data_root / name
        if path.exists():
            return cls(name, path)

    @classmethod
    def create_model(cls, registry: Registry, name: str) -> 'UserModel':
        data_root = get_data_root(registry)
        path = data_root / name
        if not path.exists():
            path.mkdir()
        return cls(name, path)

    @classmethod
    def get_models(cls, registry: Registry):
        data_root = get_data_root(registry)
        return sorted(
            (
                cls(path.name, path)
                for path in data_root.iterdir()
                if path.is_dir()
            ),
            key=lambda x: x.name,
        )


def get_authenticated_user_name(user_name, password, request):
    user_model = UserModel.get_model(request.registry, user_name)
    if user_model:
        return user_model.name
