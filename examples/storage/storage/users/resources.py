# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 24.01.2020
"""
from pyramid.security import ALL_PERMISSIONS, Allow

from restfw.hal import HalResource, HalResourceWithEmbedded, list_to_embedded_resources
from restfw.interfaces import MethodOptions
from restfw.schemas import GetEmbeddedSchema
from restfw.utils import create_validation_error
from storage.authentication.models import UserModel
from . import schemas


class User(HalResource):
    url_placeholder = '<name>'

    def __init__(self, model, parent):
        """
        :type model: UserModel
        :type parent: Users
        """
        self.model = model
        self.__parent__ = parent
        self.__name__ = model.name

    def __acl__(self):
        return [
            (Allow, self.__name__, ALL_PERMISSIONS)
        ]

    options_for_get = MethodOptions(None, schemas.UserSchema,
                                    permission='users.get')

    def as_dict(self, request):
        return {
            'name': self.__name__,
        }


class Users(HalResourceWithEmbedded):

    def __getitem__(self, key):
        request = self.get_request()
        model = UserModel.get_model(request, key)
        if model:
            return self.get_user_from_model(model)
        return super(Users, self).__getitem__(key)

    options_for_get = MethodOptions(GetEmbeddedSchema, schemas.UsersSchema, 'users.get')

    def get_embedded(self, request, params):
        users = [
            User(model, parent=self)
            for model in UserModel.get_models(request.registry)
        ]
        return list_to_embedded_resources(
            request, params, users,
            parent=self,
            embedded_name='users',
        )

    options_for_post = MethodOptions(schemas.CreateUserSchema, schemas.UserSchema, 'users.edit')

    def http_post(self, request, params):
        """
        :type request: pyramid.request.Request
        :type params: dict
        :rtype: tuple(User, bool)
        """
        name = params['name']

        if UserModel.get_model(request.registry, name):
            raise create_validation_error(
                self.options_for_post.input_schema,
                'Name "%s" is busy' % name,
                node_name='name',
            )

        model = UserModel.create_model(request, name)
        resource = self.get_user_from_model(model)
        created = True
        return resource, created

    def get_user_from_model(self, user_model):
        """
        :type user_model: UserModel
        """
        return User(user_model, parent=self)


def get_users(root):
    """
    :type root: storage.root.StorageRoot
    :rtype: Users
    """
    return root['users']
