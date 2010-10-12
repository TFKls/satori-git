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

from openid.consumer import consumer
from openid.extensions import sreg as oidsreg
from openid.extensions import pape as oidpape
from openid.extensions import ax as oidax

from satori.core.sec.tools import RightCheck, RoleSet, Token
from satori.core.sec.store import Store

from satori.objects import DispatchOn, Argument, ReturnValue, Throws
from satori.core.models import Entity, User, Login, OpenIdentity, Global, Role, Machine, Privilege
from satori.ars.wrapper import Struct, StaticWrapper, TypedMap, DefineException
from satori.ars.server import server_info

def openid_salt():
    chars = string.letters + string.digits
    salt = ''
    for i in range(16):
        salt += random.choice(chars)
    return salt

OpenIdRedirect = Struct('OpenIdRedirect', (
    ('token', Token, False),
    ('redirect', str, True),
    ('html', str, True)
))

LoginFailed = DefineException('LoginFailed', 'Invalid username or password')

security = StaticWrapper('Security')

@security.method
@Argument('s', type=str)
@ReturnValue(type=str)
def id(s):
    return s

@security.method
@Argument('token', type=Token)
@ReturnValue(type=Role)
def anonymous(token):
    globe = Global.get_instance()
    return globe.anonymous

@security.method
@Argument('token', type=Token)
@ReturnValue(type=Role)
def authenticated(token):
    globe = Global.get_instance()
    return globe.authenticated

@security.method
@Argument('token', type=Token)
@ReturnValue(type=(User, NoneType))
def whoami(token):
    if not token.valid:
        raise Exception("Provided token is expired.")
    return token.user

@security.method
@Argument('token', type=Token)
@Argument('object', type=Entity)
@Argument('right', type=str)
@ReturnValue(type=bool)
def right_have(token, object, right):
    return object.demand_right(token, right)

@security.method
@Argument('token', type=Token)
@Argument('right', type=str)
@ReturnValue(type=bool)
def global_right_have(token, right):
    return Global.get_instance().demand_right(token, right)

@security.method
@Argument('login', type=str)
@Argument('nspace', type=str) # Nie moze byc namespace - slowo kluczowe w Thrifcie
@ReturnValue(type=bool)
def login_free(login, nspace=''):
    return len(Login.objects.filter(nspace=nspace, login=login)) == 0

@security.method
@Argument('token', type=Token)
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('fullname', type=str)
@ReturnValue(type=NoneType)
def register(token, login, password, fullname):
    user = User(login=login, fullname=fullname)
    user.save()
    Privilege.grant(user, user, 'MANAGE')
    auth = Login(login=login, user=user)
    auth.set_password(password)
    auth.save()

@security.method
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('nspace', type=str) # Nie moze byc namespace - slowo kluczowe w Thrifcie
@ReturnValue(type=Token)
@Throws(LoginFailed)
def login(login, password, nspace=''):
    try:
        login = Login.objects.get(nspace=nspace, login=login)
    except Login.DoesNotExist:
        raise LoginFailed()
    if login.check_password(password):
        auth = 'login'
        if nspace != '':
            auth = auth + '.' + nspace
        return Token(user=login.user, auth=auth, validity=timedelta(hours=6))
    else:
        raise LoginFailed()

@security.method
@Argument('login', type=str)
@Argument('old_passwd', type=str)
@Argument('new_passwd', type=str) # Nie moze byc new - slowo kluczowe w Thrifcie
@Argument('nspace', type=str) # Nie moze byc namespace - slowo kluczowe w Thrifcie
@ReturnValue(type=Token)
def passwd(login, old_passwd, new_passwd, nspace=''):
    login = Login.objects.get(nspace=nspace, login=login)
    if login.change_password(old_passwd, new_passwd):
        auth = 'login'
        if nspace != '':
            auth = auth + '.' + nspace
        return Token(user=login.user, auth=auth, validity=timedelta(hours=6))
    else:
        raise Exception('Password change failed.')

def openid_realm(url):
    callback = urlparse.urlparse(url)
    return urlparse.urlunparse((callback.scheme, callback.netloc, '', '', '', ''))

def openid_modify_callback(url, salt):
    callback = urlparse.urlparse(url)
    qs = urlparse.parse_qs(callback.query)
    qs['satori.openid.salt'] = (salt,)
    query = []
    for key, vlist in qs.items():
        for value in vlist:
            query.append((key,value))
    query = urllib.urlencode(query)
    return urlparse.urlunparse((callback.scheme, callback.netloc, callback.path, callback.params, query, callback.fragment))

def openid_check_callback(url, salt):
    callback = urlparse.urlparse(url)
    qs = urlparse.parse_qs(callback.query)
    if 'satori.openid.salt' not in qs:
        return False
    if len(qs['satori.openid.salt']) != 1:
        return False
    return qs['satori.openid.salt'][0] == salt

def openid_add_ax(request):
    axr = oidax.FetchRequest()
    axr.add(oidax.AttrInfo('http://axschema.org/contact/country/home', 1, True, 'country'))
    axr.add(oidax.AttrInfo('http://axschema.org/contact/email', 1, True, 'email'))
    axr.add(oidax.AttrInfo('http://axschema.org/namePerson/first', 1, True, 'firstname'))
    axr.add(oidax.AttrInfo('http://axschema.org/namePerson/last', 1, True, 'lastname'))
    axr.add(oidax.AttrInfo('http://axschema.org/pref/language', 1, True, 'language'))
    request.addExtension(axr)

def openid_get_ax(response, identity, update =False):
    try:
        axr = oidax.FetchResponse.fromSuccessResponse(response)
        identity.country = axr.getSingle('http://axschema.org/contact/country/home', identity.country)
        identity.email = axr.getSingle('http://axschema.org/contact/email', identity.email)
        identity.language = axr.getSingle('http://axschema.org/pref/language', identity.language)
        firstname = axr.getSingle('http://axschema.org/namePerson/first', None)
        lastname = axr.getSingle('http://axschema.org/namePerson/last', None)
        if firstname != None and lastname != None:
            identity.name = firstname + ' ' + lastname
        identity.save()
        if update:
            user = identity.user
            user.fullname = identity.name
            user.save()
    except:
        pass

def openid_generic_start(openid, return_to, user_id ='', valid =1, ax =False):
    salt = openid_salt()
    session = { 'satori.openid.salt' : salt }
    store = Store()
    request = consumer.Consumer(session, store).begin(openid)
    if ax:
        openid_add_ax(request)
    redirect = ''
    html = ''
    realm = openid_realm(return_to)
    callback = openid_modify_callback(return_to, salt)
    if request.shouldSendRedirect():
        redirect = request.redirectURL(realm, callback)
    else:
        form = request.formMarkup(realm, callback, False, {'id': 'satori_openid_form'})
        html = '<html><body onload="document.getElementById(\'satori_openid_form\').submit()">' + form + '</body></html>'
    token = Token(user_id=user_id, auth='openid', data=session, validity=timedelta(hours=valid))
    return {
        'token' : token,
        'redirect' : redirect,
        'html' : html
    }

def openid_generic_finish(token, args, return_to, user =None):
    if token.auth != 'openid':
        return token
    session = token.data
    store = Store()
    response = consumer.Consumer(session, store).complete(args, return_to)
    if response.status != consumer.SUCCESS:
        raise Exception("OpenID failed.")
    callback = response.getReturnTo()
    if not openid_check_callback(callback, session['satori.openid.salt']):
        raise Exception("OpenID failed.")
    if user:
        identity = OpenIdentity(identity=response.identity_url, user=user)
        identity.save()
    else:
        identity = OpenIdentity.objects.get(identity=response.identity_url)
    openid_get_ax(response, identity, update=True)
    token = Token(user=identity.user, auth='openid', validity=timedelta(hours=6))
    return token

@security.method
@Argument('openid', type=str)
@Argument('return_to', type=str)
@ReturnValue(type=OpenIdRedirect)
def openid_login_start(openid, return_to):
    return openid_generic_start(openid=openid, return_to=return_to, user_id='', ax=True)

@security.method
@Argument('token', type=Token)
@Argument('arg_map', type=TypedMap(str, str)) # Nie moze byc args - slowo kluczowe w Thrifcie
@Argument('return_to', type=str)
@ReturnValue(type=Token)
def openid_login_finish(token, arg_map, return_to):
    return openid_generic_finish(token, arg_map, return_to)

@security.method
@Argument('login', type=str)
@Argument('openid', type=str)
@Argument('return_to', type=str)
@ReturnValue(type=OpenIdRedirect)
def openid_register_start(login, openid, return_to):
    res = openid_generic_start(openid=openid, return_to=return_to, user_id='', ax=True)
    user = User(login=login, fullname='')
    user.save()
    Privilege.grant(user, user, 'MANAGE')
    session = res['token'].data
    session['satori.openid.user'] = user.id
    res['token'].data = session
    return res

@security.method
@Argument('token', type=Token)
@Argument('arg_map', type=TypedMap(str, str)) # Nie moze byc args - slowo kluczowe w Thrifcie
@Argument('return_to', type=str)
@ReturnValue(type=Token)
def openid_register_finish(token, arg_map, return_to):
    session = token.data
    user = User.objects.get(id=session['satori.openid.user'])
    res = openid_generic_finish(token, arg_map, return_to, user)
    return res

@security.method
@Argument('login', type=str)
@Argument('password', type=str)
@Argument('openid', type=str)
@Argument('return_to', type=str)
@Argument('nspace', type=str) # Nie moze byc namespace - slowo kluczowe w Thrifcie
@ReturnValue(type=OpenIdRedirect)
def openid_add_start(login, password, openid, return_to, nspace=''):
    login = Login.objects.get(nspace=nspace, login=login)
    if login.check_password(password):
        res = openid_generic_start(openid=openid, return_to=return_to, user_id=str(token.user.id), ax=True)
        session = res['token'].data
        session['satori.openid.user'] = token.user.id
        res['token'].data = session
        return res
    raise Exception("Authorization failed.")

@security.method
@Argument('token', type=Token)
@Argument('arg_map', type=TypedMap(str, str)) # Nie moze byc args - slowo kluczowe w Thrifcie
@Argument('return_to', type=str)
@ReturnValue(type=Token)
def openid_add_finish(token, arg_map, return_to):
    session = token.data
    user = User.objects.get(id=session['satori.openid.user'])
    res = openid_generic_finish(token, arg_map, return_to, user)
    return res

@security.method
@Argument('token', type=Token)
@Argument('name', type=str)
@Argument('secret', type=str)
@Argument('address', type=str)
@Argument('netmask', type=str)
@ReturnValue(type=Machine)
def machine_register(token, name, secret, address, netmask):
    machine = Machine(login=name, fullname=name, address=address, netmask=netmask)
    machine.set_secret(secret)
    machine.save()
    return machine

@security.method
@Argument('secret', type=str)
@ReturnValue(type=Token)
def machine_login(secret):
    for machine in Machine.objects.all():
        if machine.check_ip(server_info.client_ip) and machine.check_secret(secret):
            return Token(user=machine, auth='machine', validity=timedelta(hours=24))

security._fill_module(__name__)
