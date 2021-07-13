# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""
import colander

from restfw import schemas


class UserSchema(schemas.HalResourceSchema):
    name = schemas.StringNode(title='Name')


class UsersSchema(schemas.HalResourceWithEmbeddedSchema):
    _embedded = schemas.EmbeddedNode(
        colander.SequenceSchema(
            UserSchema(title='User'),
            name='users',
            title='List of embedded users'
        ),
        missing=colander.drop
    )


class CreateUserSchema(schemas.MappingNode):
    name = schemas.StringNode(title='Name', validator=colander.Length(max=250))
