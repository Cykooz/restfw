# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 26.08.2016
"""
from zope.interface import implementer

from .interfaces import IEvent, IRoot, IRootCreated
from .typing import PyramidRequest


@implementer(IEvent)
class Event:
    request: PyramidRequest = None


@implementer(IRootCreated)
class RootCreated(Event):
    """An instance of this class is emitted after root object was created."""

    def __init__(self, root: IRoot):
        super().__init__()
        self.root = root
