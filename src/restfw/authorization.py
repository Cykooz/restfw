# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 30.03.2017
"""

from typing import Union

from pyramid.authorization import (
    ACLAllowed,
    ACLDenied,
    ALL_PERMISSIONS,
    Allow,
    Deny,
    Everyone,
)
from pyramid.location import lineage
from pyramid.util import is_nonstr_iter


ALL_GET_REQUESTS = 'get'
ALL_POST_REQUESTS = 'post'
ALL_PUT_REQUESTS = 'put'
ALL_PATCH_REQUESTS = 'patch'
ALL_DELETE_REQUESTS = 'delete'

_BASE_PERMISSIONS = {'get', 'post', 'put', 'patch', 'delete'}


class RestAclHelper:
    """A helper for use with constructing a :term:`security policy` which
    consults an :term:`ACL` object attached to a :term:`context` to determine
    authorization information about a :term:`principal` or multiple principals.
    If the context is part of a :term:`lineage`, the context's parents are
    consulted for ACL information too.
    """

    def permits(self, context, principals: Union[list, set], permission: str):
        """Return an instance of :class:`pyramid.authorization.ACLAllowed` if
        the ACL allows access a user with the given principals, return an
        instance of :class:`pyramid.authorization.ACLDenied` if not.

        When checking if principals are allowed, the security policy consults
        the ``context`` for an ACL first.  If no ACL exists on the context, or
        one does exist but the ACL does not explicitly allow or deny access for
        any of the effective principals, consult the context's parent ACL, and
        so on, until the lineage is exhausted or we determine that the policy
        permits or denies.

        During this processing, if any :data:`pyramid.authorization.Deny`
        ACE is found matching any principal in ``principals``, stop
        processing by returning an
        :class:`pyramid.authorization.ACLDenied` instance (equals
        ``False``) immediately.  If any
        :data:`pyramid.authorization.Allow` ACE is found matching any
        principal, stop processing by returning an
        :class:`pyramid.authorization.ACLAllowed` instance (equals
        ``True``) immediately.  If we exhaust the context's
        :term:`lineage`, and no ACE has explicitly permitted or denied
        access, return an instance of
        :class:`pyramid.authorization.ACLDenied` (equals ``False``).
        """
        acl = '<No ACL found on any object in resource lineage>'
        base_permission, _, context_permission = permission.partition('.')
        # base_permission - permission based on HTTP-method used to call a resource
        if base_permission and base_permission not in _BASE_PERMISSIONS:
            context_permission = permission
            base_permission = ''
        permission = context_permission

        for location in lineage(context):
            try:
                acl = location.__acl__
            except AttributeError:
                continue

            if acl and callable(acl):
                acl = acl()

            for ace in acl:
                ace_action, ace_principal, ace_permissions = ace
                if ace_principal in principals:
                    if not is_nonstr_iter(ace_permissions):
                        ace_permissions = [ace_permissions]
                    if _match_permission(permission, ace_permissions) or (
                        base_permission
                        and _match_base_permission(base_permission, ace_permissions)
                    ):
                        if ace_action == Allow:
                            return ACLAllowed(
                                ace,
                                acl,
                                permission,
                                principals,
                                location,
                            )
                        else:
                            return ACLDenied(
                                ace,
                                acl,
                                permission,
                                principals,
                                location,
                            )

        # Deny by default (if no ACL in lineage at all, or if none of the
        # principals were mentioned in any ACE we found)
        return ACLDenied('<default deny>', acl, permission, principals, context)


def principals_allowed_by_permission(context, permission: str) -> set:
    """Return the set of principals explicitly granted the
    permission named ``permission`` according to the ACL directly
    attached to the ``context`` as well as inherited ACLs based on
    the :term:`lineage`."""
    allowed = set()
    base_permission, _, context_permission = permission.partition('.')
    if base_permission and base_permission not in _BASE_PERMISSIONS:
        context_permission = permission
        base_permission = ''
    permission = context_permission

    for location in reversed(list(lineage(context))):
        # NB: we're walking *up* the object graph from the root
        try:
            acl = location.__acl__
        except AttributeError:
            continue

        allowed_here = set()
        denied_here = set()

        if acl and callable(acl):
            acl = acl()

        for ace_action, ace_principal, ace_permissions in acl:
            if not is_nonstr_iter(ace_permissions):
                ace_permissions = [ace_permissions]
            is_match = _match_permission(permission, ace_permissions) or (
                base_permission
                and _match_base_permission(base_permission, ace_permissions)
            )
            if (ace_action == Allow) and is_match:
                if ace_principal not in denied_here:
                    allowed_here.add(ace_principal)
            if (ace_action == Deny) and is_match:
                denied_here.add(ace_principal)
                if ace_principal == Everyone:
                    # clear the entire allowed set, as we've hit a
                    # deny of Everyone ala (Deny, Everyone, ALL)
                    allowed = set()
                    break
                elif ace_principal in allowed:
                    allowed.remove(ace_principal)

        allowed.update(allowed_here)

    return allowed


def _match_permission(permission, ace_permissions):
    """Match permission with list of permissions from ACE (Access Control Entries).
    If ACE permission ends with dot then it interpreted as permission prefix.
    """
    if ace_permissions is ALL_PERMISSIONS:
        return True
    for ace_permission in ace_permissions:
        if ace_permission.endswith('.') and permission.startswith(ace_permission):
            return True
        elif permission == ace_permission:
            return True
    return False


def _match_base_permission(permission, ace_permissions):
    """Match base permission with list of permissions from ACE (Access Control Entries)."""
    if ace_permissions is ALL_PERMISSIONS:
        return True
    return any(permission == ace_permission for ace_permission in ace_permissions)


def get_view_permission(http_method: str, permission: str) -> str:
    """Returns permission name for view method."""
    return f'{http_method}.{permission}' if permission else http_method
