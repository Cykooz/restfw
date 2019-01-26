# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
from __future__ import unicode_literals

import json
import logging
import os
import re
import shutil

import six
from jinja2 import Environment, PackageLoader
from pyramid.encode import urlencode
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import force_decode
from sphinx.util.docstrings import prepare_docstring
from zope.interface import provider
try:
    from pathlib import Path
except ImportError:
    # Python < 3.4
    from pathlib2 import Path

from ..usage_examples import interfaces
from ..usage_examples.collector import UsageExamplesCollector
from ..usage_examples.utils import get_relative_path


RST_METHOD_DIRECTIVES = re.compile(r'^\s*:(param|type|rtype)[^:]*:.*$', re.UNICODE).match


class RstDocGenerator(object):

    def __init__(self, web_app, prepare_env=None, principal_formatter=None, app_prefix=None, logger=None):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type prepare_env: interfaces.IPrepareEnv or None
        :type principal_formatter: interfaces.IPrincipalFormatter or None
        :type app_prefix: str or unicode or None
        :param logger: logger instance
        """
        self._collector = UsageExamplesCollector(
            web_app,
            prepare_env=prepare_env,
            principal_formatter=principal_formatter,
            docstring_extractor=docstring_extractor,
            docstring_filter=RST_METHOD_DIRECTIVES,
            logger=logger
        )
        self._app_prefix = app_prefix
        self._logger = logger or logging
        self._jinja_env = Environment(
            loader=PackageLoader('restfw.docs_gen', 'templates'),
            trim_blocks=True
        )
        self._jinja_env.filters['rst_header'] = _rst_header
        self._ep_id_2_doc_path = {}  # type: dict[str, Path]

    def _get_template(self, name):
        return self._jinja_env.get_template(name)

    def generate(self, dst_dir):
        """Generate directories and files with API documentation.
        :type dst_dir: Path
        """
        self._collector.collect()

        self._logger.info('Generate ".rst" files...')

        if not dst_dir:
            dst_dir = Path.cwd()
        if dst_dir.is_dir():
            # clear old doc
            for child in dst_dir.iterdir():
                if child.name == 'index.rst':
                    continue
                _remove_file_or_dir(child)
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)

        self._ep_id_2_doc_path = {}
        entry_points_info = self._collector.entry_points_info
        resources_info = self._collector.resources_info

        # Create directories and collect paths to entry points docs
        for ep_id, entry_point_info in six.iteritems(entry_points_info):
            app_name = self._get_app_name(entry_point_info.resource_class_name)
            app_dir_path = self._init_app_dir(app_name, dst_dir)

            resource_info = resources_info[entry_point_info.resource_class_name]
            resource_dir_path = self._init_resource_dir(resource_info, app_dir_path)

            if resource_info.count_of_entry_points > 1:
                file_name = '%s.rst' % entry_point_info.name
            else:
                file_name = 'index.rst'

            entry_point_path = resource_dir_path / file_name
            self._ep_id_2_doc_path[ep_id] = entry_point_path

        # Create .rst files with entry point documentation
        for ep_id, entry_point_info in six.iteritems(entry_points_info):
            entry_point_path = self._ep_id_2_doc_path[ep_id]
            entry_point_url = self._get_entry_point_url(ep_id)
            resource_info = resources_info[entry_point_info.resource_class_name]
            resource_description = ''
            if entry_point_path.name == 'index.rst':
                resource_description = '\n'.join(resource_info.description)

            available_methods = ', '.join('`%s`_' % m for m in entry_point_info.methods.keys())
            methods = []
            for method, method_info in six.iteritems(entry_point_info.methods):
                methods.append(
                    self._render_method_to_rst(method, method_info)
                )

            template = self._get_template('entry_point.rst')
            with entry_point_path.open('w', encoding='utf-8-sig') as f:
                text = template.render(
                    name=entry_point_info.name,
                    resource_class_name=entry_point_info.resource_class_name,
                    resource_desctiption=resource_description,
                    entry_point_url=entry_point_url,
                    resource_info=resource_info,
                    available_methods=available_methods,
                    methods=methods,
                )
                f.write(text)

    def _get_app_name(self, resource_class_name):
        if self._app_prefix and resource_class_name.startswith(self._app_prefix):
            resource_class_name = resource_class_name[len(self._app_prefix):]
        app_name = resource_class_name.split('.')[0]
        app_name = app_name.upper() if len(app_name) <= 2 else app_name.capitalize()
        return app_name

    @staticmethod
    def _get_app_dir_name(app_name):
        dir_name = app_name.replace(' ', '_').lower() + '_app'
        return dir_name

    def _init_app_dir(self, app_name, parent_dir):
        """Create directory and index.rst for application.
        :type app_name: str
        :type parent_dir: Path
        :rtype: Path
        """
        app_dir_name = self._get_app_dir_name(app_name)
        app_dir_path = parent_dir / app_dir_name
        if app_dir_path.exists():
            return app_dir_path

        # Create directory and index.rst for app
        app_dir_path.mkdir(parents=True, exist_ok=True)
        template = self._get_template('app_index.rst')
        index_path = app_dir_path / 'index.rst'
        with index_path.open('w', encoding='utf-8-sig') as f:
            text = template.render(app_name=app_name + ' App')
            f.write(text)
        return app_dir_path

    @staticmethod
    def _get_resource_name(resource_full_name):
        return resource_full_name.rsplit('.', 1)[-1]

    def _init_resource_dir(self, resource_info, parent_dir):
        """Create directory and index.rst for resource.
        :type resource_info: structs.ResourceInfo
        :type parent_dir: Path
        :rtype: Path
        """
        resource_name = self._get_resource_name(resource_info.class_name)
        resource_dir_path = parent_dir / resource_name

        if resource_dir_path.exists():
            return resource_dir_path

        # Create directory for resource
        resource_dir_path.mkdir(parents=True, exist_ok=True)
        if resource_info.count_of_entry_points <= 1:
            return resource_dir_path

        # Create special index.rst if resource has many entry points
        template = self._get_template('resource_index.rst')
        index_path = resource_dir_path / 'index.rst'
        with index_path.open('w', encoding='utf-8-sig') as f:
            text = template.render(
                resource_name=resource_name,
                resource_doc='\n'.join(resource_info.description)
            )
            f.write(text)
        return resource_dir_path

    def _get_entry_point_url(self, ep_id):
        """Returns URL of entry point formatted as restructuredText.
        :type ep_id: str
        :rtype: str
        """
        res = []
        entry_points_info = self._collector.entry_points_info
        doc_path = self._ep_id_2_doc_path[ep_id]
        entry_point_info = entry_points_info[ep_id]
        for element in entry_point_info.url_elements:
            child_ep = entry_points_info.get(element.ep_id)
            child_ep_doc_path = self._ep_id_2_doc_path.get(element.ep_id)
            value = element.value
            if child_ep and child_ep_doc_path:
                rel_path = get_relative_path(to_path=child_ep_doc_path, from_path=doc_path)
                if rel_path.endswith('.rst'):
                    rel_path = rel_path[:-4]
                value = ':doc:`{} <{}>`'.format(element.value, rel_path)
            res.append(value)
        url = '/'.join(res) or '/'
        if not url.startswith('/'):
            url = '/{}'.format(url)
        return url

    def _render_example_to_rst(self, method, example_info):
        """
        :type method: str
        :type example_info: structs.ExampleInfo
        :rtype: str
        """
        url = example_info.request_info.url
        if '_' in url:
            # Encode for restructuredText
            url = url.replace('_', '\\_')

        params = example_info.request_info.params
        if method in ('GET', 'HEAD') and params:
            url += '?' + urlencode(params, doseq=True)
            params = None

        if params:
            params = json.dumps(params, indent=2, ensure_ascii=False)

        response_headers = {}
        for header in ('Location',):
            value = example_info.response_info.headers.get(header)
            if value:
                response_headers[header] = value

        response_body = json.dumps(example_info.response_info.json_body, indent=2, ensure_ascii=False)

        title = '{} {}'.format(
            example_info.response_info.status_code,
            example_info.response_info.status_name
        )

        template = self._get_template('example.rst')
        text = template.render(
            title=title,
            method=method,
            url=url,
            headers=example_info.request_info.headers,
            params=params,
            response_status=example_info.response_info.status_code,
            response_headers=response_headers,
            response_body=response_body,
        )

        return text

    def _render_method_to_rst(self, method, method_info):
        """
        :type method: str
        :type method_info: structs.MethodInfo
        :rtype: str
        """
        examples_info = method_info.examples_info
        status_codes = sorted(set(e.response_info.status_code for e in examples_info))

        examples = []
        for status_code in status_codes:
            for example_info in examples_info:
                if example_info.response_info.status_code != status_code:
                    continue
                examples.append(
                    self._render_example_to_rst(method, example_info)
                )

        template = self._get_template('method.rst')
        text = template.render(
            method=method,
            description='\n'.join(method_info.description),
            status_codes=', '.join(str(s) for s in status_codes),
            input_schema=method_info.input_schema,
            output_schema=method_info.output_schema,
            allowed_principals=method_info.allowed_principals,
            examples=examples,
        )

        return text


def _rst_header(value, level='*'):
    if value:
        return '\n'.join([value, level * len(value)])
    return value


def _remove_file_or_dir(path):
    """
    :type path: Path
    """
    if path.is_dir():
        shutil.rmtree(bytes(path))
    else:
        os.remove(bytes(path))


@provider(interfaces.IDocStringExtractor)
def docstring_extractor(code_object):
    """Improved docstring extractor. It can determine docstring encoding.
    :type code_object: Any
    :rtype: list[unicode]
    """
    docstring = code_object.__doc__ or ''
    if not docstring:
        return []

    if not isinstance(docstring, six.text_type):
        analyzer = ModuleAnalyzer.for_module(code_object.__module__)
        docstring = force_decode(docstring, analyzer.encoding)
    return prepare_docstring(docstring)
