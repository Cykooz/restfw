# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 30.03.2017
"""
from pyramid.security import ALL_PERMISSIONS, Allow, Deny

from .vendor import pyramid_test_authorization
from ..resources import Resource


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


class TestRestACLAuthorizationPolicy(pyramid_test_authorization.TestACLAuthorizationPolicy):

    def _getTargetClass(self):
        from ..authorization import RestACLAuthorizationPolicy
        return RestACLAuthorizationPolicy

    def test_permits_with_context_aware_permission(self):
        context = DummyContext()
        policy = self._makeOne()
        assert policy.permits(context, [1], 'get')
        assert policy.permits(context, [2], 'post.dummy.create')
        assert policy.permits(context, [3], 'put.dummy.edit')
        assert policy.permits(context, [4], 'patch.dummy.patch')
        assert policy.permits(context, [5], 'delete.dummy.delete')

    def test_permits_with_permission_prefix(self):
        context = DummyContext()
        policy = self._makeOne()
        assert policy.permits(context, [6], 'post.dummy.create')
        assert policy.permits(context, [6], 'put.dummy.edit')
        assert policy.permits(context, [6], 'delete.dummy.delete')

        assert not policy.permits(context, [6], 'get')
        assert not policy.permits(context, [6], 'patch')

    def test_principals(self):
        context = DummyContext()
        policy = self._makeOne()

        principals = policy.principals_allowed_by_permission(context, 'get')
        assert principals == {1, 7}

        principals = policy.principals_allowed_by_permission(context, 'patch')
        assert principals == {4, 7}

        principals = policy.principals_allowed_by_permission(context, 'dummy.create')
        assert principals == {2, 6, 7}

        principals = policy.principals_allowed_by_permission(context, 'dummy.edit')
        assert principals == {3, 6, 7}

        principals = policy.principals_allowed_by_permission(context, 'dummy.edit')
        assert principals == {3, 6, 7}

        principals = policy.principals_allowed_by_permission(context, 'dummy.delete')
        assert principals == {5, 6, 7}

    def test_orig_permission_check(self):
        root = DummyContext()
        child = DummyContext()
        child.__parent__ = root
        child.__acl__ = []

        policy = self._makeOne()
        assert policy.permits(child, [1], 'get.child.get')

        child.__acl__ = [
            (Deny, 1, 'child.get')
        ]
        assert not policy.permits(child, [1], 'get.child.get')
