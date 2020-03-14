# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2020
"""


def runtests():
    import sys
    import pytest
    from os import environ
    from os.path import dirname, join
    cfg_path = join(dirname(dirname(__file__)), 'pytest.ini')

    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        args = args + ['storage']
    args = ['-c', cfg_path] + args
    environ['IS_TESTING'] = 'True'
    pytest.main(args)
