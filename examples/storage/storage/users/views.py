"""
:Authors: cykooz
:Date: 13.01.2021
"""

from restfw import views
from restfw.interfaces import MethodOptions
from restfw.schemas import GetEmbeddedSchema
from restfw.views import list_to_embedded_resources
from storage.authentication.models import UserModel
from . import schemas
from .resources import User, Users


@views.resource_view_config()
class UserView(views.HalResourceView):
    resource: User
    options_for_get = MethodOptions(
        None,
        schemas.UserSchema,
        permission='users.get',
    )

    def as_dict(self):
        return {
            'name': self.resource.__name__,
        }


@views.resource_view_config()
class UsersView(views.HalResourceWithEmbeddedView):
    resource: Users
    options_for_get = MethodOptions(
        GetEmbeddedSchema,
        schemas.UsersSchema,
        permission='users.get',
    )
    options_for_post = MethodOptions(
        schemas.CreateUserSchema,
        schemas.UserSchema,
        permission='users.edit',
    )

    def get_embedded(self, params: dict):
        users = [
            User(model, parent=self.resource)
            for model in UserModel.get_models(self.request.registry)
        ]
        return list_to_embedded_resources(
            self.request,
            params,
            users,
            parent=self.resource,
            embedded_name='users',
        )
