# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from zope.interface import implementer

from .interfaces import IEvent, IRootCreated, IRoot


@implementer(IEvent)
class Event(object):
    #: :type: pyramid.request.Request
    request = None


@implementer(IRootCreated)
class RootCreated(Event):
    """An instance of this class is emitted after root object was created."""

    def __init__(self, root):
        """
        :type root: IRoot
        """
        super(RootCreated, self).__init__()
        self.root = root
