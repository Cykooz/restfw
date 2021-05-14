# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.01.2020
"""
from pyramid.security import ALL_PERMISSIONS, Allow
from storage.authentication.models import UserModel
from storage.root import StorageRoot

from restfw.hal import HalResource
from restfw.typing import PyramidRequest
from restfw.utils import create_validation_error


class User(HalResource):
    url_placeholder = '<name>'

    def __init__(self, model: UserModel, parent: 'Users'):
        self.model = model
        self.__parent__ = parent
        self.__name__ = model.name

    def __acl__(self):
        return [
            (Allow, self.__name__, ALL_PERMISSIONS)
        ]


class Users(HalResource):

    def __getitem__(self, key):
        registry = self.get_registry()
        model = UserModel.get_model(registry, key)
        if model:
            return self.get_user_from_model(model)
        return super(Users, self).__getitem__(key)

    def http_post(self, request: PyramidRequest, params):
        name = params['name']

        if UserModel.get_model(request.registry, name):
            raise create_validation_error(
                self.options_for_post.input_schema,
                'Name "%s" is busy' % name,
                node_name='name',
            )

        model = UserModel.create_model(request.registry, name)
        resource = self.get_user_from_model(model)
        created = True
        return resource, created

    def get_user_from_model(self, user_model: UserModel):
        return User(user_model, parent=self)


def get_users(root: StorageRoot) -> Users:
    return root['users']
