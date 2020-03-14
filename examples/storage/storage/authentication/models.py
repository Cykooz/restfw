# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.01.2020
"""
try:
    from pathlib import Path
except ImportError:
    # Python < 3.4
    from pathlib2 import Path

from storage.main import get_data_root


class UserModel(object):

    def __init__(self, name, path):
        """
        :type name: str
        :type path: Path
        """
        self.name = name
        self.path = path

    @classmethod
    def get_model(cls, request, name):
        """
        :type request: pyramid.request.Request
        :type name: str
        :rtype: UserModel or None
        """
        data_root = get_data_root(request.registry)
        path = data_root / name
        if path.exists():
            return cls(name, path)

    @classmethod
    def create_model(cls, request, name):
        """
        :type request: pyramid.request.Request
        :type name: str
        :rtype: UserModel
        """
        data_root = get_data_root(request.registry)
        path = data_root / name
        if not path.exists():
            path.mkdir()
        return cls(name, path)

    @classmethod
    def get_models(cls, request):
        """
        :type request: pyramid.request.Request
        """
        data_root = get_data_root(request.registry)
        return sorted(
            (
                cls(path.name, path)
                for path in data_root.iterdir()
                if path.is_dir()
            ),
            key=lambda x: x.name,
        )


def get_user_principals(user_name, password, request):
    user_model = UserModel.get_model(request, user_name)
    if user_model:
        return [user_model.name]
