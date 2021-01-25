"""
:Authors: cykooz
:Date: 13.01.2021
"""
from restfw.testing import assert_resource
from .. import usage_examples


def test_file(web_app, pyramid_request):
    resource_info = usage_examples.FileExamples(pyramid_request)
    assert_resource(resource_info, web_app)


def test_files(web_app, pyramid_request):
    resource_info = usage_examples.FilesExamples(pyramid_request)
    assert_resource(resource_info, web_app)
