# vim:ts=4:sts=4:sw=4:expandtab
"""
Security and authorization procedures.
"""

from types import NoneType

from satori.core.sec.tools import CheckRights, RoleSet, Token, authenticateByLogin, authenticateByOpenIdStart, authenticateByOpenIdFinish
from satori.core.sec.store import Store

from satori.objects import DispatchOn, Argument, ReturnValue
from satori.core.models import Object as modelObject, User
from satori.ars.wrapper import Struct, StaticWrapper, TypedMap

OpenIdRedirect = Struct('OpenIdRedirect', (
    ('token', str, False),
    ('redirect', str, True),
    ('html', str, True)
))

security = StaticWrapper('Security')

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
@Argument('args', type=TypedMap(str, str))
@Argument('return_to', type=str)
@ReturnValue(type=str)
def openIdFinish(token, args, return_to):
    return authenticateByOpenIdFinish(token, args, return_to)

@security.method
@Argument('login', type=str)
@ReturnValue(type=bool)
def check_login(login):
    return len(User.objects.filter(login=login)) == 0

@security.method
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('fullname', type=str)
@ReturnValue(type=NoneType)
def register(login, password, fullname):
    user = User()
    user.login = login
    user.fullname = fullname
    user.save()
    auth = Login()
    auth.login = login
    auth.user = user
    auth.password = crypt.crypt(password, str(random.randint(100000, 999999)))
    auth.save()

security._fill_module(__name__)

