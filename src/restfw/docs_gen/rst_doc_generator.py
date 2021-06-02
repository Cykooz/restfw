# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
import dataclasses
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import ChoiceLoader, Environment, PackageLoader
from pyramid.encode import urlencode
from sphinx.util.docstrings import prepare_docstring
from zope.interface import provider

from ..testing.webapp import WebApp
from ..usage_examples import interfaces
from ..usage_examples.collector import UsageExamplesCollector
from ..usage_examples.utils import get_relative_path


@dataclasses.dataclass()
class PackagePrefix:
    prefix: str
    name: str
    slug: str


class RstDocGenerator(object):
    """Utility for generate rst-files (reStructuredText) with a documentation
    based of information collected from usage examples.
    """

    def __init__(self, web_app: WebApp, prepare_env=None, principal_formatter=None,
                 package_prefixes: Optional[List[PackagePrefix]] = None, templates_loader=None, logger=None):
        """
        :type web_app: restfw.testing.webapp.WebApp
        :type prepare_env: interfaces.IPrepareEnv or None
        :type principal_formatter: interfaces.IPrincipalFormatter or None
        :param templates_loader: Jinja2 templates loader to overwrite all or some templates
        :type templates_loader: jinja2.loaders.BaseLoader or None
        :param logger: logger instance
        """
        self._collector = UsageExamplesCollector(
            web_app,
            prepare_env=prepare_env,
            principal_formatter=principal_formatter,
            docstring_extractor=docstring_extractor,
            logger=logger
        )
        self._package_prefixes = package_prefixes or []
        self._logger = logger or logging

        loader = PackageLoader('restfw.docs_gen', 'templates')
        if templates_loader:
            loader = ChoiceLoader([
                templates_loader,
                loader,
            ])
        self._jinja_env = Environment(loader=loader, trim_blocks=True)
        self._jinja_env.filters['rst_header'] = _rst_header
        self._ep_id_2_doc_path: Dict[str, Path] = {}

    def generate(self, dst_dir: Path):
        """Generate directories and files with API documentation."""
        self._collector.collect()

        self._logger.info('Generate ".rst" files...')
        dst_dir = self._prepare_dst_directory(dst_dir)
        self._create_dirs_and_collect_ep_paths(dst_dir)
        self._create_entry_points_rst()

    @staticmethod
    def _prepare_dst_directory(dst_dir: Path):
        """Create destination directory or remove all it children except 'index.rst'."""
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
        return dst_dir

    def _create_dirs_and_collect_ep_paths(self, dst_dir: Path):
        """Create directories and collect paths to entry points docs."""
        self._ep_id_2_doc_path = {}
        resources_info = self._collector.resources_info

        for ep_id, entry_point_info in self._collector.entry_points_info.items():
            class_name = entry_point_info.examples_class_name
            app_dir_path = self._init_app_dir(class_name, dst_dir)

            resource_info = resources_info[entry_point_info.resource_class_name]
            resource_dir_path = self._init_resource_dir(resource_info, app_dir_path)

            if resource_info.count_of_entry_points > 1:
                file_name = '%s.rst' % entry_point_info.name
            else:
                file_name = 'index.rst'

            entry_point_path = resource_dir_path / file_name
            self._ep_id_2_doc_path[ep_id] = entry_point_path

    def _create_entry_points_rst(self):
        """Create .rst files with entry point documentation."""
        resources_info = self._collector.resources_info

        for ep_id, entry_point_info in self._collector.entry_points_info.items():
            entry_point_path = self._ep_id_2_doc_path[ep_id]
            entry_point_url = self._get_entry_point_url(ep_id)
            resource_info = resources_info[entry_point_info.resource_class_name]
            resource_description = ''
            if entry_point_path.name == 'index.rst':
                resource_description = '\n'.join(resource_info.description)

            available_methods = ', '.join('`%s`_' % m for m in entry_point_info.methods.keys())
            methods = []
            for method, method_info in entry_point_info.methods.items():
                methods.append(
                    self._render_method_to_rst(method, method_info)
                )

            template = self._get_template('entry_point.rst')
            with entry_point_path.open('w', encoding='utf-8-sig') as f:
                text = template.render(
                    name=entry_point_info.name,
                    resource_class_name=entry_point_info.resource_class_name,
                    resource_description=resource_description,
                    entry_point_url=entry_point_url,
                    resource_info=resource_info,
                    available_methods=available_methods,
                    methods=methods,
                )
                f.write(text)

    def _get_template(self, name):
        return self._jinja_env.get_template(name)

    def _get_app_info(self, class_name):
        package_name = ''
        package_slug = ''
        for package_prefix in self._package_prefixes:
            prefix = package_prefix.prefix
            if prefix and class_name.startswith(prefix):
                package_name = package_prefix.name
                package_slug = package_prefix.slug
                class_name = class_name[len(prefix):]
                break
        class_package = class_name.partition('.')[0]
        app_slug = class_package.replace(' ', '_').lower()
        app_name = class_package.replace('_', ' ')
        app_name = app_name.upper() if len(app_name) <= 2 else app_name.title()
        package_dir_name = f'{package_slug}_pkg' if package_slug else ''
        app_dir_name = f'{app_slug}_app'
        return package_name, package_dir_name, app_dir_name, app_name

    def _init_app_dir(self, class_name, parent_dir):
        """Create a directory and index.rst for application.
        :type class_name: str
        :type parent_dir: Path
        :rtype: Path
        """
        package_name, package_dir_name, app_dir_name, app_name = self._get_app_info(class_name)
        if package_dir_name:
            package_dir_path = parent_dir / package_dir_name
            if not package_dir_path.exists():
                # Create a directory and index.rst for package
                package_dir_path.mkdir(parents=True, exist_ok=True)
                template = self._get_template('package_index.rst')
                index_path = package_dir_path / 'index.rst'
                with index_path.open('w', encoding='utf-8-sig') as f:
                    text = template.render(package_name=package_name)
                    f.write(text)

        if package_dir_name:
            app_dir_path = parent_dir / package_dir_name / app_dir_name
        else:
            app_dir_path = parent_dir / app_dir_name
        if not app_dir_path.exists():
            # Create a directory and index.rst for app
            app_dir_path.mkdir(parents=True, exist_ok=True)
            template = self._get_template('app_index.rst')
            index_path = app_dir_path / 'index.rst'
            with index_path.open('w', encoding='utf-8-sig') as f:
                text = template.render(package_name=package_name, app_name=app_name + ' App')
                f.write(text)

        return app_dir_path

    @staticmethod
    def _get_resource_name(resource_full_name):
        return resource_full_name.rsplit('.', 1)[-1]

    def _init_resource_dir(self, resource_info, parent_dir):
        """Create directory and index.rst for resource.
        :type resource_info: restfw.usage_examples.structs.ResourceInfo
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
        :type example_info: restfw.usage_examples.structs.ExampleInfo
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
        expected_headers = example_info.response_info.expected_headers or {}
        interested_headers = sorted({'Location'}.union(expected_headers.keys()))
        for header in interested_headers:
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
            description=example_info.description,
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
        :type method_info: restfw.usage_examples.structs.MethodInfo
        :rtype: str
        """
        examples_info = method_info.examples_info
        status_codes = sorted(set(e.response_info.status_code for e in examples_info))

        examples = []
        for status_code in status_codes:
            descriptions = set()
            for example_info in examples_info:
                if example_info.exclude_from_doc:
                    continue
                if example_info.response_info.status_code != status_code:
                    continue
                if example_info.description in descriptions:
                    # Do not render example with duplicate description
                    continue
                if example_info.description is not None:
                    descriptions.add(example_info.description)
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
def docstring_extractor(code_object) -> List[str]:
    docstring = code_object.__doc__ or ''
    if not docstring:
        return []
    return prepare_docstring(docstring)
