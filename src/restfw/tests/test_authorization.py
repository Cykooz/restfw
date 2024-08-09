# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 30.03.2017
"""

import unittest

from pyramid.authorization import ALL_PERMISSIONS, Allow, DENY_ALL, Deny, Everyone

from .vendor import pyramid_test_authorization as vendor_test
from ..authorization import RestAclHelper, principals_allowed_by_permission
from ..resources import Resource


class RestDummyContext(Resource):
    __acl__ = [
        (Allow, 1, 'get'),
        (Allow, 2, 'dummy.create'),
        (Allow, 3, 'dummy.edit'),
        (Allow, 4, 'patch'),
        (Allow, 5, 'dummy.delete'),
        (Allow, 6, 'dummy.'),
        (Allow, 7, ALL_PERMISSIONS),
    ]


class TestRestAclHelper(unittest.TestCase):
    # Tests copied from pyramid TestAclHelper

    def test_no_acl(self):
        context = vendor_test.DummyContext()
        helper = RestAclHelper()
        result = helper.permits(context, ['foo'], 'permission')
        self.assertEqual(result, False)
        self.assertEqual(result.ace, '<default deny>')
        self.assertEqual(result.acl, '<No ACL found on any object in resource lineage>')
        self.assertEqual(result.permission, 'permission')
        self.assertEqual(result.principals, ['foo'])
        self.assertEqual(result.context, context)

    def test_acl(self):
        from pyramid.authorization import (
            ALL_PERMISSIONS,
            DENY_ALL,
            Allow,
            Authenticated,
            Deny,
            Everyone,
        )

        helper = RestAclHelper()
        root = vendor_test.DummyContext()
        community = vendor_test.DummyContext(__name__='community', __parent__=root)
        blog = vendor_test.DummyContext(__name__='blog', __parent__=community)
        root.__acl__ = [(Allow, Authenticated, vendor_test.VIEW)]
        community.__acl__ = [
            (Allow, 'fred', ALL_PERMISSIONS),
            (Allow, 'wilma', vendor_test.VIEW),
            DENY_ALL,
        ]
        blog.__acl__ = [
            (Allow, 'barney', vendor_test.MEMBER_PERMS),
            (Allow, 'wilma', vendor_test.VIEW),
        ]

        result = helper.permits(blog, [Everyone, Authenticated, 'wilma'], 'view')
        self.assertEqual(result, True)
        self.assertEqual(result.context, blog)
        self.assertEqual(result.ace, (Allow, 'wilma', vendor_test.VIEW))
        self.assertEqual(result.acl, blog.__acl__)

        result = helper.permits(blog, [Everyone, Authenticated, 'wilma'], 'delete')
        self.assertEqual(result, False)
        self.assertEqual(result.context, community)
        self.assertEqual(result.ace, (Deny, Everyone, ALL_PERMISSIONS))
        self.assertEqual(result.acl, community.__acl__)

        result = helper.permits(blog, [Everyone, Authenticated, 'fred'], 'view')
        self.assertEqual(result, True)
        self.assertEqual(result.context, community)
        self.assertEqual(result.ace, (Allow, 'fred', ALL_PERMISSIONS))
        result = helper.permits(
            blog, [Everyone, Authenticated, 'fred'], 'doesntevenexistyet'
        )
        self.assertEqual(result, True)
        self.assertEqual(result.context, community)
        self.assertEqual(result.ace, (Allow, 'fred', ALL_PERMISSIONS))
        self.assertEqual(result.acl, community.__acl__)

        result = helper.permits(blog, [Everyone, Authenticated, 'barney'], 'view')
        self.assertEqual(result, True)
        self.assertEqual(result.context, blog)
        self.assertEqual(result.ace, (Allow, 'barney', vendor_test.MEMBER_PERMS))
        result = helper.permits(blog, [Everyone, Authenticated, 'barney'], 'administer')
        self.assertEqual(result, False)
        self.assertEqual(result.context, community)
        self.assertEqual(result.ace, (Deny, Everyone, ALL_PERMISSIONS))
        self.assertEqual(result.acl, community.__acl__)

        result = helper.permits(root, [Everyone, Authenticated, 'someguy'], 'view')
        self.assertEqual(result, True)
        self.assertEqual(result.context, root)
        self.assertEqual(result.ace, (Allow, Authenticated, vendor_test.VIEW))
        result = helper.permits(blog, [Everyone, Authenticated, 'someguy'], 'view')
        self.assertEqual(result, False)
        self.assertEqual(result.context, community)
        self.assertEqual(result.ace, (Deny, Everyone, ALL_PERMISSIONS))
        self.assertEqual(result.acl, community.__acl__)

        result = helper.permits(root, [Everyone], 'view')
        self.assertEqual(result, False)
        self.assertEqual(result.context, root)
        self.assertEqual(result.ace, '<default deny>')
        self.assertEqual(result.acl, root.__acl__)

        context = vendor_test.DummyContext()
        result = helper.permits(context, [Everyone], 'view')
        self.assertEqual(result, False)
        self.assertEqual(result.ace, '<default deny>')
        self.assertEqual(result.acl, '<No ACL found on any object in resource lineage>')

    def test_string_permissions_in_acl(self):
        helper = RestAclHelper()
        root = vendor_test.DummyContext()
        root.__acl__ = [(Allow, 'wilma', 'view_stuff')]

        result = helper.permits(root, ['wilma'], 'view')
        # would be True if matching against 'view_stuff' instead of against
        # ['view_stuff']
        self.assertEqual(result, False)

    def test_callable_acl(self):
        helper = RestAclHelper()
        context = vendor_test.DummyContext()
        fn = lambda self: [(Allow, 'bob', 'read')]
        context.__acl__ = fn.__get__(context, context.__class__)
        result = helper.permits(context, ['bob'], 'read')
        self.assertTrue(result)

    def test_principals_allowed_by_permission_direct(self):
        context = vendor_test.DummyContext()
        acl = [
            (Allow, 'chrism', ('read', 'write')),
            DENY_ALL,
            (Allow, 'other', 'read'),
        ]
        context.__acl__ = acl
        result = sorted(principals_allowed_by_permission(context, 'read'))
        self.assertEqual(result, ['chrism'])

    def test_principals_allowed_by_permission_callable_acl(self):
        context = vendor_test.DummyContext()
        acl = lambda: [
            (Allow, 'chrism', ('read', 'write')),
            DENY_ALL,
            (Allow, 'other', 'read'),
        ]
        context.__acl__ = acl
        result = sorted(principals_allowed_by_permission(context, 'read'))
        self.assertEqual(result, ['chrism'])

    def test_principals_allowed_by_permission_string_permission(self):
        context = vendor_test.DummyContext()
        acl = [(Allow, 'chrism', 'read_it')]
        context.__acl__ = acl
        result = principals_allowed_by_permission(context, 'read')
        # would be ['chrism'] if 'read' were compared against 'read_it' instead
        # of against ['read_it']
        self.assertEqual(list(result), [])

    def test_principals_allowed_by_permission(self):
        root = vendor_test.DummyContext(__name__='', __parent__=None)
        community = vendor_test.DummyContext(__name__='community', __parent__=root)
        blog = vendor_test.DummyContext(__name__='blog', __parent__=community)
        root.__acl__ = [
            (Allow, 'chrism', ('read', 'write')),
            (Allow, 'other', ('read',)),
            (Allow, 'jim', ALL_PERMISSIONS),
        ]
        community.__acl__ = [
            (Deny, 'flooz', 'read'),
            (Allow, 'flooz', 'read'),
            (Allow, 'mork', 'read'),
            (Deny, 'jim', 'read'),
            (Allow, 'someguy', 'manage'),
        ]
        blog.__acl__ = [(Allow, 'fred', 'read'), DENY_ALL]

        result = sorted(principals_allowed_by_permission(blog, 'read'))
        self.assertEqual(result, ['fred'])
        result = sorted(principals_allowed_by_permission(community, 'read'))
        self.assertEqual(result, ['chrism', 'mork', 'other'])
        result = sorted(principals_allowed_by_permission(root, 'read'))
        self.assertEqual(result, ['chrism', 'jim', 'other'])

    def test_principals_allowed_by_permission_no_acls(self):
        context = vendor_test.DummyContext()
        result = sorted(principals_allowed_by_permission(context, 'read'))
        self.assertEqual(result, [])

    def test_principals_allowed_by_permission_deny_not_permission_in_acl(self):
        context = vendor_test.DummyContext()
        acl = [(Deny, Everyone, 'write')]
        context.__acl__ = acl
        result = sorted(principals_allowed_by_permission(context, 'read'))
        self.assertEqual(result, [])

    def test_principals_allowed_by_permission_deny_permission_in_acl(self):
        context = vendor_test.DummyContext()
        acl = [(Deny, Everyone, 'read')]
        context.__acl__ = acl
        result = sorted(principals_allowed_by_permission(context, 'read'))
        self.assertEqual(result, [])

    # Additional tests

    def test_permits_with_context_aware_permission(self):
        context = RestDummyContext()
        helper = RestAclHelper()
        assert helper.permits(context, [1], 'get')
        assert helper.permits(context, [2], 'post.dummy.create')
        assert helper.permits(context, [3], 'put.dummy.edit')
        assert helper.permits(context, [4], 'patch.dummy.patch')
        assert helper.permits(context, [5], 'delete.dummy.delete')

    def test_permits_with_permission_prefix(self):
        context = RestDummyContext()
        helper = RestAclHelper()
        assert helper.permits(context, [6], 'post.dummy.create')
        assert helper.permits(context, [6], 'put.dummy.edit')
        assert helper.permits(context, [6], 'delete.dummy.delete')

        assert not helper.permits(context, [6], 'get')
        assert not helper.permits(context, [6], 'patch')

    def test_principals(self):
        context = RestDummyContext()

        principals = principals_allowed_by_permission(context, 'get')
        assert principals == {1, 7}

        principals = principals_allowed_by_permission(context, 'patch')
        assert principals == {4, 7}

        principals = principals_allowed_by_permission(context, 'dummy.create')
        assert principals == {2, 6, 7}

        principals = principals_allowed_by_permission(context, 'dummy.edit')
        assert principals == {3, 6, 7}

        principals = principals_allowed_by_permission(context, 'dummy.edit')
        assert principals == {3, 6, 7}

        principals = principals_allowed_by_permission(context, 'dummy.delete')
        assert principals == {5, 6, 7}

    def test_orig_permission_check(self):
        root = RestDummyContext()
        child = RestDummyContext()
        child.__parent__ = root
        child.__acl__ = []

        helper = RestAclHelper()
        assert helper.permits(child, [1], 'get.child.get')

        child.__acl__ = [(Deny, 1, 'child.get')]
        assert not helper.permits(child, [1], 'get.child.get')
