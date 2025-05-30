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

from restfw.interfaces import IResource
from restfw.typing import PyramidRequest
from restfw.views import get_resource_view


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
                    if _match_permission(
                        base_permission, context_permission, ace_permissions
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
            is_match = _match_permission(
                base_permission, context_permission, ace_permissions
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


"""
Matrix of options for matching the required permission with
the permission specified in the resource's ACL.

b - base permission (http method)
c - context permission (permission of resource)

    Req. | [] | b1     | c1        | b1.c1                |
ACL      |    |        |           |                      |      
---------|----|--------|-----------|----------------------|
[]       | F  | F      | F         | F                    |
b2       | F  | b1==b2 | F         | b1==b2               |
c2       | F  | F      | c1.sw(c2) | c1.sw(c2)            |
b2.c2    | F  | F      | F         | b1==b2 and c1.sw(c2) |
"""


def _match_permission(base_permission, context_permission, ace_permissions):
    """Match permission with the list of permissions from ACE (Access Control Entries).
    If ACE permission ends with a dot, then it is interpreted as a permission prefix.
    """
    if ace_permissions is ALL_PERMISSIONS:
        return True
    if not base_permission and not context_permission:
        return False

    for ace_permission in ace_permissions:
        ace_base_permission, _, ace_context_permission = ace_permission.partition('.')
        if not ace_base_permission and not ace_context_permission:
            continue
        if ace_base_permission and ace_base_permission not in _BASE_PERMISSIONS:
            ace_context_permission = ace_permission
            ace_base_permission = ''

        if ace_base_permission and base_permission != ace_base_permission:
            continue

        if _match_context_permission(context_permission, ace_context_permission):
            return True

    return False


def _match_context_permission(permission: str, ace_permission: str) -> bool:
    if not ace_permission or permission == ace_permission:
        return True
    return ace_permission.endswith('.') and permission.startswith(ace_permission)


def _match_base_permission(permission, ace_permissions):
    """Match base permission with list of permissions from ACE (Access Control Entries)."""
    if ace_permissions is ALL_PERMISSIONS:
        return True
    return any(permission == ace_permission for ace_permission in ace_permissions)


def get_view_permission(http_method: str, permission: str) -> str:
    """Returns permission name for view method."""
    return f'{http_method}.{permission}' if permission else http_method


def has_view_access(
    request: PyramidRequest,
    context,
    http_method: str,
) -> bool:
    if view := get_resource_view(context, request):
        options_name = f'options_for_{http_method}'
        if options := getattr(view, options_name, None):
            if permission := options.permission:
                permission = f'{http_method}.{permission}'
                return request.has_permission(permission, context=context)
    return False
