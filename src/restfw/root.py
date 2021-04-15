# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from pyramid.registry import Registry
from pyramid.security import Allow, DENY_ALL, Everyone
from zope.interface import implementer

from .authorization import ALL_GET_REQUESTS
from .events import RootCreated
from .hal import SimpleContainer
from .interfaces import IRoot
from .utils import notify


@implementer(IRoot)
class Root(SimpleContainer):
    __acl__ = [
        (Allow, Everyone, ALL_GET_REQUESTS),
        DENY_ALL
    ]

    def __init__(self, registry: Registry):
        super(Root, self).__init__()
        self.registry = registry


def root_factory(request, root_class=Root):
    root = getattr(request.registry, '_restfw_root', None)
    if not root:
        root = root_class(registry=request.registry)
        request.registry._restfw_root = root
        notify(RootCreated(root), request)
    return root
