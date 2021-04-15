"""
:Authors: cykooz
:Date: 13.01.2021
"""
from cykooz.testing import ANY, D
from pyramid.httpexceptions import HTTPForbidden, HTTPUnauthorized

from restfw.usage_examples import UsageExamples, examples_config
from .resources import Files
from ..users.testing import create_user


@examples_config()
class FileExamples(UsageExamples):
    default_auth = 'user:'

    def prepare_resource(self):
        create_user(self.request, 'admin')
        create_user(self.request, 'other_user')
        user = create_user(self.request, 'user')
        files: Files = user['files']
        file_resource = files['readme.txt']
        file_resource.model.write(b'Hello\nWorld!')
        return file_resource

    def get_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='other_user:', exception=HTTPForbidden())

        self.send(
            result={
                '_links': {
                    'self': {'href': ANY},
                },
                'name': 'readme.txt',
                'size': 12,
            },
        )

    def put_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='other_user:', exception=HTTPForbidden())

        self.send(
            params='New file content',
            headers={
                'Content-Type': 'text/plain',
            },
            result={
                '_links': {
                    'self': {'href': ANY},
                },
                'name': 'readme.txt',
                'size': 18,  # len('"New file content"')
            },
        )

    def delete_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='other_user:', exception=HTTPForbidden())
        self.send(status=204)


@examples_config()
class FilesExamples(UsageExamples):
    default_auth = 'user:'

    def prepare_resource(self):
        create_user(self.request, 'admin')
        create_user(self.request, 'other_user')
        user = create_user(self.request, 'user')
        files: Files = user['files']
        for i in range(3):
            file_resource = files[f'readme{i}.txt']
            file_resource.model.write(b'Hello\nWorld!')
        return files

    def get_requests(self):
        self.send(auth='', exception=HTTPUnauthorized())
        self.send(auth='bad_user:', exception=HTTPUnauthorized())
        self.send(auth='other_user:', exception=HTTPForbidden())

        self.send(
            params={'total_count': True, 'limit': 2},
            result={
                '_links': {
                    'self': {'href': self.resource_url},
                    'next': D(),
                },
                '_embedded': {
                    'files': [
                        D({'name': 'readme1.txt', 'size': 12}),
                        D({'name': 'readme2.txt', 'size': 12}),
                    ]
                }
            },
            result_headers=D({'X-Total-Count': '3'})
        )
