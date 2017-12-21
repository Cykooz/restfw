# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.08.2017
"""
from .utils import is_testing_env


class TestingPredicate(object):

    def __init__(self, val, config):
        self.val = val
        self.result = val == is_testing_env(config.registry)

    def text(self):
        return 'testing = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        return self.result
