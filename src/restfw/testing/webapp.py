# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 15.11.2016
"""
from __future__ import absolute_import, print_function

import inspect
import warnings
from os.path import basename

import requests
from pyramid import httpexceptions
from pyramid.encode import urlencode
from requests.exceptions import RequestException
from webtest import TestApp
from webtest.utils import NoDefault

from ..utils import force_dict_utf8


class WebApp(object):

    def __init__(self, app_env_fabric, url_prefix=''):
        self.app_env_fabric = app_env_fabric
        self.env = None
        self.registry = None
        self._root = None
        self._request = None
        self.test_app = None
        self.url_prefix = url_prefix.strip('/')

    @property
    def request(self):
        warnings.warn(
            'Property "WebApp.request" will be removed at next major release of "restfw". '
            'Please use context manager "open_pyramid_request" to get pyramid request instance.',
            stacklevel=2
        )
        return self._request

    @property
    def root(self):
        warnings.warn(
            'Property "WebApp.root" will be removed at next major release of "restfw". '
            'Please use context manager "open_pyramid_request" to get root instance form '
            'pyramid request as "request.root".',
            stacklevel=2
        )
        return self._root

    def __enter__(self):
        self.env = self.app_env_fabric()
        self.registry = self.env['registry']
        #: :type: restfw.root.Root
        self._request = self.env['request']
        self._request.root = self._root = self.env['root']
        app = self.env['app']
        self.test_app = TestApp(app)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.registry = None
        self._request = None
        self._root = None
        if self.env:
            self.env['closer']()
        self.env = None
        self.test_app = None

    def _format_error(self, title, response, method_name, url, **kwargs):
        res = [
            title,
            '{} {}'.format(method_name.upper(), url),
        ]
        for key, value in kwargs.items():
            if value:
                value = str(value)
                if len(value) > 512:
                    value = value[:512] + '...'
                res.append('{}: {}'.format(key, value))
        body = response.text if hasattr(response, 'body') else response.content
        body = body.strip()
        if len(body) > 512:
            body = body[:512] + '...'
        res.append('Response Body: %s' % body)
        return '\n'.join(res)

    def _check_status(self, response, method_name, url, status, **kwargs):
        if status is None:
            assert 200 <= response.status_code < 400, self._format_error(
                'Response status is bad.',
                response, method_name, url, **kwargs)
        else:
            assert response.status_code == status, self._format_error(
                'Response status is bad.',
                response, method_name, url, **kwargs)

    def _check_error_code(self, response, method_name, url, exception, **kwargs):
        code = description = detail = None
        if exception:
            status = exception.code
            if status >= 400:
                description = exception.explanation or exception.title
                if inspect.isclass(exception):
                    code = exception.__name__
                else:
                    code = exception.__class__.__name__
                    detail = exception.detail
                if code.startswith('HTTP'):
                    code = code[4:]

        if code and method_name != 'head':
            json_body = response.json_body
            assert 'code' in json_body
            assert json_body['code'] == code, self._format_error(
                'Code of error is not equal to required.',
                response, method_name, url, **kwargs)
            assert json_body['description'] == description, self._format_error(
                'Description of error is not equal to required.',
                response, method_name, url, **kwargs)
            if detail is not None:
                assert json_body['detail'] == detail, self._format_error(
                    'Detail of error is not equal to required.',
                    response, method_name, url, **kwargs)

    def _app_method(self, method_name, url, params=None,
                    exception=None, headers=None,
                    content_type=None, upload_files=None, status=None,
                    check_response=True, **kwargs):
        """
        :rtype: webtest.TestResponse
        """
        if not url.startswith(('/', 'http://', 'https://')):
            url = '/%s/%s' % (self.url_prefix, url.lstrip('/'))
        headers = headers or {}
        kwargs['headers'] = headers

        if content_type and method_name not in {'get', 'head', 'options'}:
            kwargs['content_type'] = content_type
        if upload_files:
            kwargs['upload_files'] = upload_files

        http_method = getattr(self.test_app, method_name, None)
        assert http_method is not None, 'Unknown HTTP method: %s' % method_name

        if method_name == 'head':
            head_url = url
            if params:
                # TastApp.head() is not support `params` argument
                if isinstance(params, dict):
                    params = urlencode(params)
                head_url += '?' + params
            response = http_method(head_url, status='*', **kwargs)
            kwargs['params'] = params
        else:
            if method_name != 'options':
                kwargs['params'] = params
            response = http_method(url, status='*', **kwargs)

        if check_response:
            if exception:
                status = exception.code
            self._check_status(response, method_name, url, status, **kwargs)
            self._check_error_code(response, method_name, url, exception, **kwargs)
        return response

    def head(self, url, params='', **kwargs):
        return self._app_method('head', url, params=params, **kwargs)

    def options(self, url, **kwargs):
        kwargs['params'] = None
        return self._app_method('options', url, **kwargs)

    def get(self, url, **kwargs):
        return self._app_method('get', url, **kwargs)

    def post(self, url, params='', **kwargs):
        return self._app_method('post', url, params=params, **kwargs)

    def post_json(self, url, params=NoDefault, **kwargs):
        if params is None or params is NoDefault:
            params = {}
        return self._app_method('post_json', url, params=params, **kwargs)

    def put(self, url, params='', **kwargs):
        return self._app_method('put', url, params=params, **kwargs)

    def put_json(self, url, params=NoDefault, **kwargs):
        if params is None or params is NoDefault:
            params = {}
        return self._app_method('put_json', url, params=params, **kwargs)

    def patch(self, url, params='', **kwargs):
        return self._app_method('patch', url, params=params, **kwargs)

    def patch_json(self, url, params=NoDefault, **kwargs):
        if params is None or params is NoDefault:
            params = {}
        return self._app_method('patch_json', url, params=params, **kwargs)

    def delete(self, url, params='', **kwargs):
        return self._app_method('delete', url, params=params, **kwargs)

    def delete_json(self, url, params=NoDefault, **kwargs):
        if params is None or params is NoDefault:
            params = {}
        return self._app_method('delete_json', url, params=params, **kwargs)

    # Helper methods

    def _send_file_to_external(self, file_path, url, params=None, headers=None, method='post'):
        params = params if params is not None else {}
        headers = headers if headers is not None else {}
        params = force_dict_utf8(params)
        headers = force_dict_utf8(headers)
        files = {'file': (basename(file_path), open(file_path, 'rb'))}
        upload_attempts = 2

        while True:
            try:
                if method == 'put':
                    params = files['file'][1].read()
                    r = requests.put(url, data=params, headers=headers,
                                     allow_redirects=False)
                else:
                    r = requests.post(url, data=params,
                                      files=files, allow_redirects=False)

                if r.status_code == 303:
                    redirect_url = r.headers['Location']
                    assert redirect_url.startswith('http://localhost/')
                    redirect_url = redirect_url[len('http://localhost'):]
                    r = self.post(redirect_url)
                return r
            except RequestException as error:
                upload_attempts -= 1
                if upload_attempts == 0:
                    print('=' * 40)
                    print('RequestException during file upload to external storage\n %s' % error)
                    print('=' * 40)
                    raise

    def _send_file_to_local(self, file_path, url, params=None, headers=None, method='post'):
        params = params if params is not None else {}
        headers = headers if headers is not None else {}

        if url.startswith('http://localhost/'):
            url = url[len('http://localhost'):]

        if method == 'post':
            params = params.copy()
            return self.post(url, params=params, upload_files=[('file', file_path)],
                             headers=headers)
        elif method == 'put':
            with open(file_path, 'rb') as data_file:
                data = data_file.read()
                return self.put(url, params=data, headers=headers,
                                content_type='application/octet-stream')

    def send_file(self, file_path, url, params=None, headers=None,
                  method='post', exception=httpexceptions.HTTPOk):
        file_upload_headers = headers.copy()
        if url.startswith('http://localhost/') or url.startswith('/%s/' % self.url_prefix):
            response = self._send_file_to_local(file_path, url, params=params, headers=file_upload_headers,
                                                method=method)
        else:
            response = self._send_file_to_external(file_path, url, params=params, headers=file_upload_headers,
                                                   method=method)

        if response.status_code >= 300:
            self._check_status(response, method, url, exception.code, params=None, headers=None)

        return response

    def download_file(self, url, exception=httpexceptions.HTTPOk, expected_headers=None):
        if url.startswith('http://localhost/'):
            url = url[len('http://localhost'):]
        if url.startswith('/%s/' % self.url_prefix):
            r = self.get(url, exception=exception)
            headers = dict(r.headers)
            content = r.body
        else:
            r = requests.get(url)
            self._check_status(r, 'get', url, status=exception.code)
            headers = dict(r.headers)
            content = r.content
        if expected_headers is not None:
            assert headers == expected_headers
        return content
