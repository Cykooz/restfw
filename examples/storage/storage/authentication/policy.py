"""
:Authors: cykooz
:Date: 12.07.2021
"""
from pyramid.authentication import extract_http_basic_credentials
from pyramid.authorization import Authenticated, Everyone
from pyramid.interfaces import ISecurityPolicy
from zope.interface import implementer

from restfw.authorization import RestAclHelper
from restfw.typing import PyramidRequest
from .models import get_authenticated_user_name


@implementer(ISecurityPolicy)
class ExampleSecurityPolicy:
    realm = 'Storage Example'

    def __init__(self):
        self.helper = RestAclHelper()

    def identity(self, request: PyramidRequest):
        credentials = extract_http_basic_credentials(request)
        if credentials:
            user_name = get_authenticated_user_name(
                credentials.username,
                credentials.password,
                request,
            )
            return user_name

    def authenticated_userid(self, request: PyramidRequest):
        return request.identity

    def permits(self, request: PyramidRequest, context, permission):
        principals = {Everyone}
        identity = request.identity
        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity)
        return self.helper.permits(context, principals, permission)

    def remember(self, request: PyramidRequest, userid, **kw):
        pass

    def forget(self, request: PyramidRequest, **kw):
        return [('WWW-Authenticate', 'Basic realm="%s"' % self.realm)]
