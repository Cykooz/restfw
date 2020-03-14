# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2020
"""
from functools import partial

from pyramid.config import Configurator
from pyramid.settings import asbool

from restfw.root import root_factory as base_root_factory

try:
    from pathlib import Path
except ImportError:
    # Python < 3.4
    from pathlib2 import Path


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['testing'] = asbool(global_config.get('testing', False))
    settings['is_doc_building'] = asbool(global_config.get('is_doc_building', False))
    settings.setdefault('pyramid.includes', [
        'restfw',
        'storage.authentication',
        'storage.users',
        'storage.files',
    ])

    from .root import StorageRoot
    root_factory = partial(base_root_factory, root_class=StorageRoot)

    with Configurator(settings=settings, root_factory=root_factory) as config:
        data_root = Path(settings['storage.data_root'])
        admin_dir = data_root / 'admin'
        admin_dir.mkdir(parents=True, exist_ok=True)
        config.registry.data_root = data_root

    return config.make_wsgi_app()


def get_data_root(registry):
    """
    :type registry: pyramid.registry.Registry
    :rtype: Path
    """
    return registry.data_root
