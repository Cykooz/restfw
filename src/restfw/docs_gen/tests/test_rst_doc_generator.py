# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 19.10.2020
"""

import logging
import os
from pathlib import Path

from ..rst_doc_generator import PackagePrefix, RstDocGenerator
from ...tests.test_usage_examples_collector import (
    Dummy1Examples,
    DummyContainerExamples,
    prepare_env,
)


def test_doc_generator(web_app, app_config, tmpdir):
    logger = logging.getLogger('test_doc_generator')
    logging.disable(logging.CRITICAL)
    temp_dir = Path(tmpdir)

    # Without usage examples
    generator = RstDocGenerator(web_app, prepare_env=prepare_env, logger=logger)
    generator.generate(temp_dir)
    assert os.listdir(temp_dir) == []

    # Register usage examples fabrics
    app_config.add_usage_examples_fabric(Dummy1Examples)
    app_config.add_usage_examples_fabric(DummyContainerExamples)
    app_config.commit()
    generator = RstDocGenerator(web_app, prepare_env=prepare_env, logger=logger)
    generator.generate(temp_dir)
    assert os.listdir(temp_dir) == ['restfw_app']
    restfw_app_dir = temp_dir / 'restfw_app'
    assert restfw_app_dir.is_dir()
    assert sorted(os.listdir(restfw_app_dir)) == [
        'DummyContainer',
        'DummyResource',
        'index.rst',
    ]

    resource_dir = restfw_app_dir / 'DummyResource'
    assert restfw_app_dir.is_dir()
    assert sorted(os.listdir(resource_dir)) == ['index.rst']

    # With packages
    generator = RstDocGenerator(
        web_app,
        prepare_env=prepare_env,
        package_prefixes=[
            PackagePrefix(prefix='restfw.', name='RestFW Applications', slug='restfw'),
        ],
        logger=logger,
    )
    generator.generate(temp_dir)
    assert os.listdir(temp_dir) == ['restfw_pkg']
    package_dir = temp_dir / 'restfw_pkg'
    assert package_dir.is_dir()
    assert sorted(os.listdir(package_dir)) == ['index.rst', 'tests_app']

    app_dir = package_dir / 'tests_app'
    assert app_dir.is_dir()
    assert sorted(os.listdir(app_dir)) == [
        'DummyContainer',
        'DummyResource',
        'index.rst',
    ]

    resource_dir = app_dir / 'DummyResource'
    assert resource_dir.is_dir()
    assert sorted(os.listdir(resource_dir)) == ['index.rst']
