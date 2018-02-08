# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 28.04.2015
"""
import os
import re

import six
from pyramid.location import lineage
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import force_decode
from sphinx.util.docstrings import prepare_docstring


def is_doc_building():
    # type: (pyramid.registry.Registry) -> bool
    return os.environ.get('BUILD_DOCS', '').lower() in ('true', '1', 'y')


def get_resource_class_name(resource):
    class_name = resource.__class__.__module__
    return '{}.{}'.format(class_name, resource.__class__.__name__)


def get_resource_name(resource_full_name):
    return resource_full_name.rsplit('.', 1)[-1]


def get_app_name(resource, cut_class_prefix='mountbit.backend.'):
    resource_class_name = get_resource_class_name(resource)
    if resource_class_name.startswith(cut_class_prefix):
        resource_class_name = resource_class_name[len(cut_class_prefix):]
    app_name = resource_class_name.split('.')[0]
    app_name = app_name.upper() if len(app_name) <= 2 else app_name.capitalize()
    return app_name


def get_app_dir_name(app_name):
    dir_name = app_name.replace(' ', '_').lower() + '_app'
    return dir_name


def get_resource_url(resource, plain_text=False, cut_class_prefix='mountbit.backend.'):
    elements = []
    links = []
    for resource in lineage(resource):
        name = getattr(resource, 'url_placeholder', None)
        if not name:
            name = resource.__name__ or ''
        class_name = get_resource_class_name(resource)
        if not class_name.startswith('mountbit.restfw.resources.PersistentContainer'):
            app_dir_name = get_app_dir_name(get_app_name(resource, cut_class_prefix))
            resource_name = get_resource_name(class_name)
            links.append('../../{}/{}/index'.format(app_dir_name, resource_name))
        else:
            links.append('')
        elements.append(name)
    elements.reverse()
    elements = elements[3:]
    links.reverse()
    links = links[3:]
    res = []
    for name, link in zip(elements, links):
        if link and not plain_text:
            name = ':doc:`{} <{}>`'.format(name, link)
        res.append(name)
    url = '/'.join(res) or '/'
    if not url.startswith('/'):
        url = '/{}'.format(url)
    return url


def resource_description(resource):
    docstring = resource.__class__.__doc__ or ''
    if not docstring:
        return
    if not isinstance(docstring, six.text_type):
        analyzer = ModuleAnalyzer.for_module(resource.__class__.__module__)
        docstring = force_decode(docstring, analyzer.encoding)
    for line in prepare_docstring(docstring):
        yield line


RST_METHOD_DIRECTIVES = re.compile('^\s*:(param|type|rtype)[^:]*:.*$', re.UNICODE)


def method_description(method):
    docstring = method.__doc__ or ''
    if not isinstance(docstring, six.text_type):
        analyzer = ModuleAnalyzer.for_module(method.__module__)
        docstring = force_decode(docstring, analyzer.encoding)
    for line in prepare_docstring(docstring):
        if not RST_METHOD_DIRECTIVES.match(line):
            yield line


def header(text, level='*'):
    yield text
    yield level * len(text)
    yield ''


def raw(text, format_type='html', indent=0):
    space = ' ' * indent
    yield '{}.. raw:: {}'.format(space, format_type)
    yield ''
    for line in text.split('\n'):
        yield '{}  {}'.format(space, line)
    yield ''
