# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.01.2019
"""
from mountbit.utils.testing import ANY

from restfw.usage_examples.interfaces import IUsageExamplesFabric
from restfw.usage_examples import UsageExamples


class Dummy1Examples(UsageExamples):

    def prepare_resource(self):
        return self.root


class Dummy2Examples(UsageExamples):

    def prepare_resource(self):
        return self.root


def test_add_usage_examples_fabric(app_config, pyramid_request):
    registry = app_config.registry

    assert list(registry.getUtilitiesFor(IUsageExamplesFabric)) == []

    app_config.add_usage_examples_fabric(Dummy1Examples)
    assert list(registry.getUtilitiesFor(IUsageExamplesFabric)) == []

    app_config.commit()
    assert list(registry.getUtilitiesFor(IUsageExamplesFabric)) == [
        ('restfw.tests.test_add_usage_examples_fabric.Dummy1Examples', ANY),
    ]

    app_config.add_usage_examples_fabric(Dummy2Examples)
    assert list(registry.getUtilitiesFor(IUsageExamplesFabric)) == [
        ('restfw.tests.test_add_usage_examples_fabric.Dummy1Examples', ANY),
    ]

    app_config.commit()
    assert sorted(registry.getUtilitiesFor(IUsageExamplesFabric)) == [
        ('restfw.tests.test_add_usage_examples_fabric.Dummy1Examples', ANY),
        ('restfw.tests.test_add_usage_examples_fabric.Dummy2Examples', ANY),
    ]
