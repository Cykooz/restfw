# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.08.2017
"""
from .utils import is_debug, is_testing


class TestingPredicate(object):

    def __init__(self, val, config):
        self.val = val
        self.result = val == is_testing(config.registry)

    def text(self):
        return 'testing = %s' % (self.val,)

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result


class DebugPredicate(object):

    def __init__(self, val, config):
        self.val = val
        self.result = val == is_debug(config.registry)

    def text(self):
        return 'debug = %s' % (self.val,)

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result


class DebugOrTestingPredicate(object):

    def __init__(self, val, config):
        self.val = val
        self.result = val == (is_debug(config.registry) or is_testing(config.registry))

    def text(self):
        return 'debug_or_testing = %s' % (self.val,)

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result
