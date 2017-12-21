# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 07.07.2016
"""
from __future__ import print_function

import argparse
import codecs
import os
import shutil
from collections import defaultdict
from io import StringIO

from jinja2 import Environment, PackageLoader
from mountbit.backend.mongodb.utils import clear_mongodb
from mountbit.backend.redis.utils import clear_redis_dbs
from mountbit.backend.testing.webapp import WebApp
from mountbit.restfw.interfaces import IResourceInfoFabric
from mountbit.utils import working_directory

from . import utils
from .generator import get_resource_doc
from .jinja_filters import rst_header


class EntryPoint(object):

    def __init__(self, name, resource_class, doc):
        self.name = name
        self.resource_class = resource_class
        self.doc = doc


class DocResource(object):

    def __init__(self, resource_narrative_doc=None):
        self.resource_narrative_doc = resource_narrative_doc
        self.entry_points = {}


def generate_docs():
    parser = argparse.ArgumentParser(description='Generate API docs')
    parser.add_argument('path', help='path where create documentation files')
    args = parser.parse_args()

    path = args.path
    if not path:
        path = os.getcwd()
    if os.path.isdir(path):
        for name in os.listdir(path):
            if name == 'index.rst':
                continue
            path_for_remove = os.path.join(path, name)
            if os.path.isdir(path_for_remove):
                shutil.rmtree(path_for_remove)
            else:
                os.remove(path_for_remove)
    else:
        os.makedirs(path)

    os.environ['BUILD_DOCS'] = 'true'

    jinja_env = Environment(loader=PackageLoader('mountbit.backend.docs', 'templates'))
    jinja_env.filters['rst_header'] = rst_header

    with working_directory(path), WebApp(is_doc_building='true') as web_app:
        registry = web_app.registry
        root = web_app.root
        apps = defaultdict(lambda: defaultdict(DocResource))
        for _, fabric in registry.getUtilitiesFor(IResourceInfoFabric):
            web_app.tasks_queue.clear()
            clear_mongodb()
            clear_redis_dbs(web_app.registry)
            #: :type: mountbit.restfw.resource_info.ResourceInfo
            resource_info = fabric(registry, root)
            resource_full_name = utils.get_resource_class_name(resource_info.resource)
            app_name = utils.get_app_name(resource_info.resource)
            entry_point_path = utils.get_resource_url(resource_info.resource, plain_text=True)

            entry_point_name = fabric.__name__
            if entry_point_name.endswith('Info'):
                entry_point_name = entry_point_name[:-4]
            print('Collecting "%s" entry point from "%s" application.' % (entry_point_name, app_name))

            with StringIO() as f:
                for line in get_resource_doc(web_app, resource_info):
                    if isinstance(line, str):
                        line = line.decode('utf-8')
                    f.write(line)
                    f.write(u'\n')
                entry_point = EntryPoint(
                    name=entry_point_name,
                    resource_class=resource_full_name,
                    doc=f.getvalue()
                )
                #: :type: DocResource
                doc_resource = apps[app_name][resource_full_name]
                if doc_resource.resource_narrative_doc is None:
                    doc_resource.resource_narrative_doc = '\n'.join(utils.resource_description(resource_info.resource))
                doc_resource.entry_points[entry_point_path] = entry_point

        print('\nGenerate ".rst" files.')
        app_names = sorted(apps.keys())
        for app_name in app_names:
            app_dir_name = utils.get_app_dir_name(app_name)
            os.mkdir(app_dir_name)
            with working_directory(app_dir_name):
                template = jinja_env.get_template('app_index.rst')
                with codecs.open('index.rst', 'w', 'utf-8-sig') as f:
                    text = template.render(app_name=app_name + ' App')
                    f.write(text)

                for resource_full_name, doc_resource in apps[app_name].iteritems():
                    resource_name = utils.get_resource_name(resource_full_name)
                    os.mkdir(resource_name)
                    entry_points = doc_resource.entry_points
                    with working_directory(resource_name):
                        resource_doc = doc_resource.resource_narrative_doc
                        if len(entry_points) > 1:
                            template = jinja_env.get_template('resource_index.rst')
                            with codecs.open('index.rst', 'w', 'utf-8-sig') as f:
                                text = template.render(
                                    resource_name=resource_name,
                                    resource_doc=resource_doc
                                )
                                f.write(text)
                            resource_doc = ''

                        for entry_point_path, entry_point in entry_points.iteritems():
                            template = jinja_env.get_template('entry_point.rst')
                            if len(entry_points) > 1:
                                file_name = '%s.rst' % entry_point.name
                            else:
                                file_name = 'index.rst'
                            with codecs.open(file_name, 'w', 'utf-8-sig') as f:
                                text = template.render(
                                    entry_point=entry_point,
                                    entry_point_path=entry_point_path,
                                    resource_doc=resource_doc
                                )
                                f.write(text)
