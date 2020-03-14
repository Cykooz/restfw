# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
from cykooz.testing import ANY, D
from pyramid.httpexceptions import HTTPForbidden, HTTPUnauthorized

from restfw.testing import basic_auth_value
from restfw.usage_examples import UsageExamples, examples_config
from .resources import get_users
from .testing import create_user


@examples_config()
class UsersExamples(UsageExamples):
    headers_for_listing = {'Authorization': basic_auth_value('admin', '')}

    def prepare_resource(self):
        create_user(self.request, 'admin')
        for i in range(2):
            create_user(self.request, 'user%d' % i)
        return get_users(self.root)

    def get_requests(self, send):
        send(exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('bad_user', '')}, exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('user0', '')}, exception=HTTPForbidden())

        send(
            params={'total_count': True, 'limit': 2},
            headers={'Authorization': basic_auth_value('admin', '')},
            result={
                '_links': {
                    'self': {'href': self.resource_url},
                    'next': D(),
                },
                '_embedded': {
                    'users': [
                        D({'name': 'admin'}),
                        D({'name': 'user0'}),
                    ]
                }
            },
            result_headers=D({'X-Total-Count': '3'})
        )

    def post_requests(self, send):
        send(exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('bad_user', '')}, exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('user0', '')}, exception=HTTPForbidden())

        send(
            params={'name': 'new_user'},
            headers={'Authorization': basic_auth_value('admin', '')},
            result={
                '_links': {
                    'self': {'href': ANY},
                },
                'name': 'new_user',
            },
            status=201,
        )


@examples_config()
class UserExamples(UsageExamples):

    def prepare_resource(self):
        create_user(self.request, 'admin')
        create_user(self.request, 'other_user')
        return create_user(self.request, 'user')

    def get_requests(self, send):
        send(exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('bad_user', '')}, exception=HTTPUnauthorized())
        send(headers={'Authorization': basic_auth_value('other_user', '')}, exception=HTTPForbidden())

        send(
            headers={'Authorization': basic_auth_value('user', '')},
            result={
                '_links': {
                    'self': {'href': ANY},
                },
                'name': 'user',
            },
        )
