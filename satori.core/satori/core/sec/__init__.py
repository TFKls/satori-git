# vim:ts=4:sts=4:sw=4:expandtab
"""
Security and authorization procedures.
"""
from satori.core.sec.tools import CheckRights, RoleSet, Token, authenticateByLogin, authenticateByOpenIdStart, authenticateByOpenIdFinish
from satori.core.sec.store import Store

from satori.objects import DispatchOn, Argument, ReturnValue
from satori.core.models import Object as modelObject, User
from satori.ars import django_
import typed

OpenIdRedirect = django_.StructType('OpenIdRedirect', (
    ('token', str, False),
    ('redirect', str, True),
    ('html', str, True)
))

class SecurityOpers(django_.Opers):
    security = django_.StaticProceduresProvider('Security')

    @security.method
    @Argument('token', type=Token)
    @ReturnValue(type=User)
    def whoami(token):
        return token.user

    @security.method
    @Argument('token', type=Token)
    @Argument('object', type=modelObject)
    @Argument('right', type=str)
    @ReturnValue(type=bool)
    def cani_impl(token, object, right):
        checker = CheckRights()
        roleset = RoleSet(token.user)
        return checker.check(roleset, object, right)

    @security.method
    @Argument('login', type=str)
    @Argument('password', type=str)
    @ReturnValue(type=str)
    def login(login, password):
        return authenticateByLogin(login, password)

    @security.method
    @Argument('openid', type=str)
    @Argument('realm', type=str)
    @Argument('return_to', type=str)
    @ReturnValue(type=OpenIdRedirect)
    def openIdStart(openid, realm, return_to):
        return authenticateByOpenIdStart(openid, realm, return_to)

    @security.method
    @Argument('token', type=Token)
    @Argument('args', type=typed.Dict(typed.String, typed.String))
    @Argument('return_to', type=str)
    @ReturnValue(type=str)
    def openIdFinish(token, args, return_to):
        return authenticateByOpenIdFinish(token, args, return_to)


