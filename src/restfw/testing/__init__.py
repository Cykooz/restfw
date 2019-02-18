# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 06.12.2016
"""
import base64

from ..utils import force_utf8


try:
    import pytest
    pytest.register_assert_rewrite(
        'restfw.testing.resource_testing',
        'restfw.testing.webapp',
    )
except (ImportError, AttributeError):
    pass

from .resource_testing import assert_resource


def basic_auth_value(user_name, password):
    auth_str = force_utf8(u'%s:%s' % (user_name, password))
    return b'Basic {}'.format(base64.b64encode(auth_str))
