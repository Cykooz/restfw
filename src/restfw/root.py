# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from pyramid.security import DENY_ALL, Allow, Everyone
from pyramid.threadlocal import get_current_request
from zope.interface import implementer

from .events import RootCreated
from .hal import SimpleContainer
from .interfaces import IRoot
from .utils import notify


@implementer(IRoot)
class Root(SimpleContainer):

    __acl__ = [
        (Allow, Everyone, 'get'),
        DENY_ALL
    ]

    @property
    def request(self):
        """
        :rtype: pyramid.request.Request
        """
        return get_current_request()


def bootstrap(request, root_class=Root):
    root = root_class()
    notify(RootCreated(root), request)
    return root


def root_factory(request, root_class=Root):
    root = getattr(request.registry, '_restfw_root', None)
    if not root:
        root = bootstrap(request, root_class)
        request.registry._restfw_root = root
    return root
