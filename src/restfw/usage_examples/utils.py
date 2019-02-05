# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 25.01.2019
"""
from __future__ import print_function, unicode_literals

import re
import sys

import six
from zope.interface import provider


try:
    from pathlib import Path
except ImportError:
    # Python < 3.4
    from pathlib2 import Path

from . import interfaces


def get_relative_path(to_path, from_path, from_file=True):
    """Return string with relative path to given to_path from given from_path.
    :type to_path: Path
    :type from_path: Path
    :type from_file: bool
    :rtype: str

    >>> to_path = Path('/root/dir1/subdir1/file.txt')
    >>> print(get_relative_path(to_path, Path('/root/dir2/subdir2/image.jpg')))
    ../../dir1/subdir1/file.txt

    >>> print(get_relative_path(to_path, Path('/root/dir1/subdir1/image.jpg')))
    file.txt

    >>> print(get_relative_path(to_path, Path('/root/dir1/subdir2'), from_file=False))
    ../subdir1/file.txt

    >>> print(get_relative_path(to_path, to_path))
    file.txt

    >>> print(get_relative_path(to_path, to_path, from_file=False))
    .
    """
    from_path = from_path.absolute()
    to_path = to_path.absolute()
    if from_path == to_path:
        return to_path.name if from_file else '.'

    from_parts = from_path.parts
    to_parts = to_path.parts

    for i, (from_part, to_part) in enumerate(zip(from_parts, to_parts)):
        if from_part != to_part:
            from_parts = from_parts[i:]
            to_parts = to_parts[i:]
            break

    backs_count = len(from_parts)
    if from_file and backs_count > 0:
        backs_count -= 1
    res = ['..'] * backs_count
    res.extend(to_parts)
    return '/'.join(res)


@provider(interfaces.IDocStringExtractor)
def default_docstring_extractor(code_object):
    """Convert a docstring into lines of text. Remove common leading
    indentation, where the indentation of a given number of lines
    (usually just one) is ignored.

    An empty line is added to act as a separator between this docstring
    and following content.

    :param code_object: object of code (function, method or class)
    :rtype: list[unicode]
    """
    docstring = code_object.__doc__ or ''
    if not docstring:
        return []

    if not isinstance(docstring, six.text_type):
        docstring = docstring.decode('utf-8')

    ignore = 1
    lines = docstring.expandtabs().splitlines()
    # Find minimum indentation of any non-blank lines after ignored lines.
    margin = sys.maxsize
    for line in lines[ignore:]:
        content = len(line.lstrip())
        if content:
            indent = len(line) - content
            margin = min(margin, indent)
    # Remove indentation from ignored lines.
    for i in range(ignore):
        if i < len(lines):
            lines[i] = lines[i].lstrip()
    if margin < sys.maxsize:
        for i in range(ignore, len(lines)):
            lines[i] = lines[i][margin:]
    # Remove any leading blank lines.
    while lines and not lines[0]:
        lines.pop(0)
    # make sure there is an empty line at the end
    if lines and lines[-1]:
        lines.append('')
    return lines


RST_METHOD_DIRECTIVES = re.compile(r'^\s*:(param|type|rtype|return)[^:]*:.*$', re.UNICODE).match


@provider(interfaces.IDocStringLineFilter)
def sphinx_doc_filter(line):
    return bool(RST_METHOD_DIRECTIVES(line))
