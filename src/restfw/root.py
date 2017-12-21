# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 20.08.2016
"""
from pyramid.security import DENY_ALL, Allow, Everyone
from pyramid_zodbconn import get_connection
from transaction.interfaces import AlreadyInTransaction
from zope.interface import implementer

from .events import RootCreated
from .hal import PersistentContainer
from .interfaces import IRoot
from .utils import notify


@implementer(IRoot)
class Root(PersistentContainer):

    __acl__ = [
        (Allow, Everyone, 'get'),
        DENY_ALL
    ]

    _v_request = None

    @property
    def request(self):
        """
        :rtype: pyramid.request.Request
        """
        return self._v_request

    def set_request(self, request):
        """
        :type request: pyramid.request.Request
        """
        self._v_request = request


def bootstrap(zodb_root, request, root_class=Root):
    if 'app_root' not in zodb_root:
        root = root_class()
        zodb_root['app_root'] = root
        notify(RootCreated(root), request)
    root = zodb_root['app_root']
    root._v_request = request
    return root


def root_factory(request, root_class=Root):
    conn = get_connection(request)
    try:
        with request.tm:
            return bootstrap(conn.root(), request, root_class)
    except AlreadyInTransaction:
        return bootstrap(conn.root(), request, root_class)
