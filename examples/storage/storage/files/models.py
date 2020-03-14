# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 05.03.2020
"""
try:
    from pathlib import Path
except ImportError:
    # Python < 3.4
    from pathlib2 import Path


class FileModel(object):

    def __init__(self, path):
        """
        :type path: Path
        """
        self._path = path
        self.name = path.name

    @property
    def exists(self):
        return self._path.exists()

    @property
    def size(self):
        """
        :rtype: int or None
        """
        if self.exists:
            return self._path.stat().st_size

    def create(self):
        self._path.touch()

    def write(self, data):
        with self._path.open('wb') as f:
            f.write(data)

    def delete(self):
        if self.exists:
            self._path.unlink()
