# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 21.01.2019
"""
from restfw.utils import get_object_fullname


def test_get_object_fullname():
    assert get_object_fullname(get_object_fullname) == 'restfw.utils.get_object_fullname'
