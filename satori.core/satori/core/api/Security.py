# vim:ts=4:sts=4:sw=4:expandtab
"""
Security and authorization procedures.
"""

from datetime import datetime, timedelta
from types import NoneType
import string
import random
import urlparse
import urllib

from satori.core.sec.tools import RightCheck, RoleSet, Token
from satori.core.sec.store import Store

from satori.objects import DispatchOn, Argument, ReturnValue
from satori.core.models import Object, User, Login
from satori.ars.wrapper import Struct, StaticWrapper, TypedMap

def _salt():
    chars = string.letters + string.digits
    salt = ''
    for i in range(8):
        salt += random.choice(chars)
    return salt

OpenIdRedirect = Struct('OpenIdRedirect', (
    ('token', Token, False),
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
@Argument('object', type=Object)
@Argument('right', type=str)
@ReturnValue(type=bool)
def right_have(token, object, right):
    checker = RightCheck()
    roleset = RoleSet(token=token)
    return checker(roleset, object, right)

@security.method
@Argument('login', type=str)
@Argument('namespace', type=str, default='')
@ReturnValue(type=bool)
def login_free(login, namespace):
    return len(Login.objects.filter(namespace=namespace, login=login)) == 0

@security.method
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('fullname', type=str)
@ReturnValue(type=User)
def register(login, password, fullname):
    user = User(login=login, fullname=fullname)
    user.save()
    auth = Login(login=login, user=user)
    auth.set_password(password)
    auth.save()
    return user

@security.method
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('namespace', type=str, default='')
@ReturnValue(type=Token)
def login(login, password, namespace):
    login = Login.objects.get(namespace=namespace, login=login)
    if login.check_password(password):
        auth = 'login'
        if namespace != '':
            auth = auth + '.' + namespace
    	return Token(user=login.user, auth=auth, validity=timedelta(hours=6))

@security.method
@Argument('openid', type=str)
@Argument('realm', type=str)
@Argument('return_to', type=str)
@ReturnValue(type=OpenIdRedirect)
def openid_start(openid, realm, return_to):
    session = { 'id' : _salt() }
    store = Store()
    callback = urlparse.urlparse(return_to)
    qs = urlparse.parse_qs(callback.query)
    qs['__satori__openid'] = [ session['id'] ]
    query = []
    for key, vlist in qs.items():
        for value in vlist:
        	query.append((key,value))
    query = urllib.urlencode(query)
    url = urlparse.urlunparse((callback.scheme, callback.netloc, callback.path, callback.params, query, callback.fragment))
    cons = consumer.Consumer(session, store)
    request = cons.begin(openid)
    #request.addExtension
    redirect = ''
    html = ''
    if request.shouldSendRedirect():
        redirect = request.redirectURL(realm, url)
    else:
        form = request.formMarkup(realm, url, False, {'id': 'openid_form'})
        html = '<html><body onload="document.getElementById(\'openid_form\').submit()">' + form + '</body></html>'
    token = Token(user_id='', auth='openid', data=session, validity=timedelta(hours=1)) 
    return {
        'token' : token,
        'redirect' : redirect,
        'html' : html
    }

@security.method
@Argument('token', type=Token)
@Argument('args', type=TypedMap(str, str))
@Argument('return_to', type=str)
@ReturnValue(type=Token)
def openid_finish(token, args, return_to):
    if token.auth != 'openid':
        return token
    session = token.data
    store = Store()
    cons = consumer.Consumer(session, store)
    response = cons.complete(args, return_to)
    if response.status != consumer.SUCCESS:
        raise "OpenID failed."
    identity = OpenIdentity.objects.get(identity=response.identity_url)
    token = Token(user=identity.user, auth='openid', validity=timedelta(hours=6)) 
    return token

security._fill_module(__name__)

