# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 14.03.2020
"""
from restfw.testing import assert_resource
from .. import usage_examples


def test_users(web_app, pyramid_request):
    resource_info = usage_examples.UsersExamples(pyramid_request)
    assert_resource(resource_info, web_app)


def test_user(web_app, pyramid_request):
    resource_info = usage_examples.UserExamples(pyramid_request)
    assert_resource(resource_info, web_app)
