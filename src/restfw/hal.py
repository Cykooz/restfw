# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 13.12.2017
"""
from pyramid.interfaces import ILocation
from zope.interface import implementer

from . import interfaces
from .resources import Resource


@implementer(interfaces.IHalResource)
class HalResource(Resource):
    pass


class SimpleContainer(HalResource):

    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        try:
            return self._data[key]
        except KeyError:
            return super(SimpleContainer, self).__getitem__(key)

    def __setitem__(self, key, value):
        if ILocation.providedBy(value):
            value.__name__ = key
            value.__parent__ = self
        return self._data.__setitem__(key, value)

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()
