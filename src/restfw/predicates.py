# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.08.2017
"""

from pyramid.interfaces import IPredicateInfo

from .utils import is_debug, is_testing


class TestingPredicate:
    def __init__(self, val, info: IPredicateInfo):
        self.val = val
        self.result = val == is_testing(info.registry)

    def text(self):
        return f'testing = {self.val}'

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result


class DebugPredicate:
    def __init__(self, val, info: IPredicateInfo):
        self.val = val
        self.result = val == is_debug(info.registry)

    def text(self):
        return f'debug = {self.val}'

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result


class DebugOrTestingPredicate:
    def __init__(self, val, info: IPredicateInfo):
        self.val = val
        self.result = val == (is_debug(info.registry) or is_testing(info.registry))

    def text(self):
        return f'debug_or_testing = {self.val}'

    phash = text

    def __call__(self, *args, **kwargs):
        return self.result
