# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.04.2017
"""


def rst_header(value, level='*'):
    if value:
        return '\n'.join([value, level * len(value)])
    return value
