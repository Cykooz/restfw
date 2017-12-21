# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 30.03.2017
"""
from pyramid.security import Allow, ALL_PERMISSIONS
from pyramid.tests.test_authorization import TestACLAuthorizationPolicy

from ..resources import Resource
from ..interfaces import MethodOptions


class DummyContext(Resource):

    __acl__ = [
        (Allow, 1, 'get'),
        (Allow, 2, 'dummy.create'),
        (Allow, 3, 'dummy.edit'),
        (Allow, 4, 'patch'),
        (Allow, 5, 'dummy.delete'),
        (Allow, 6, 'dummy.'),
        (Allow, 7, ALL_PERMISSIONS),
    ]

    options_for_get = MethodOptions(None, None)
    options_for_post = MethodOptions(None, None, 'dummy.create')
    options_for_put = MethodOptions(None, None, 'dummy.edit')
    options_for_patch = None
    options_for_delete = MethodOptions(None, None, 'dummy.delete')


class TestRestACLAuthorizationPolicy(TestACLAuthorizationPolicy):

    def _getTargetClass(self):
        from ..authorization import RestACLAuthorizationPolicy
        return RestACLAuthorizationPolicy

    def test_permits_with_context_aware_permission(self):
        context = DummyContext()
        policy = self._makeOne()
        assert policy.permits(context, [1], 'get')
        assert policy.permits(context, [2], 'post')
        assert policy.permits(context, [3], 'put')
        assert policy.permits(context, [4], 'patch')
        assert policy.permits(context, [5], 'delete')

    def test_permits_with_permission_prefix(self):
        context = DummyContext()
        policy = self._makeOne()
        assert policy.permits(context, [6], 'post')
        assert policy.permits(context, [6], 'put')
        assert policy.permits(context, [6], 'delete')

        assert not policy.permits(context, [6], 'get')
        assert not policy.permits(context, [6], 'patch')
