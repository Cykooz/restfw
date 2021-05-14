# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 23.01.2020
"""


def runtests():
    import sys
    import pytest
    from pathlib import Path
    from os import environ
    cfg_path = str(Path(__file__).parent.parent / 'setup.cfg')

    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        args += ['--pyargs', 'storage']
    args = ['-c', cfg_path] + args
    environ['IS_TESTING'] = 'true'

    return pytest.main(args)
