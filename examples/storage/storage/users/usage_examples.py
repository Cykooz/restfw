"""
:Authors: cykooz
:Date: 14.03.2020
"""
from cykooz.testing import ANY, D
from pyramid.httpexceptions import HTTPForbidden, HTTPUnauthorized

from restfw.usage_examples import UsageExamples, examples_config
from .resources import get_users
from .testing import create_user


@examples_config()
class UsersExamples(UsageExamples):
    default_auth = 'admin:'

    def prepare_resource(self):
        create_user(self.request, 'admin')
        for i in range(2):
            create_user(self.request, 'user%d' % i)
        return get_users(self.root)

    def get_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='user0:', exception=HTTPForbidden())

        self.send(
            params={'total_count': True, 'limit': 2},
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

    def post_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='user0:', exception=HTTPForbidden())

        self.send(
            params={'name': 'new_user'},
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
    default_auth = 'user:'

    def prepare_resource(self):
        create_user(self.request, 'admin')
        create_user(self.request, 'other_user')
        return create_user(self.request, 'user')

    def get_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='other_user:', exception=HTTPForbidden())

        self.send(
            result={
                '_links': {
                    'self': {'href': ANY},
                },
                'name': 'user',
            },
        )
