# vim:ts=4:sts=4:sw=4:expandtab

import crypt
import hashlib
import random
import string

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

LoginFailed = DefineException('LoginFailed', 'Invalid username or password')
InvalidLogin = DefineException('InvalidLogin', 'The specified login \'{login}\' is invalid: {reason}',
    [('login', unicode, False), ('reason', unicode, False)])
InvalidEmail = DefineException('InvalidEmail', 'The specified email \'{email}\' is invalid: {reason}',
    [('email', unicode, False), ('reason', unicode, False)])
InvalidPassword = DefineException('InvalidPassword', 'The specified password is invalid: {reason}',
    [('reason', unicode, False)])

def login_ok(login):
    if not login:
        raise InvalidLogin(login=login, reason='is empty')
    if len(login) < 3:
        raise InvalidLogin(login=login, reason='is too short')
    if len(login) > 24:
        raise InvalidLogin(login=login, reason='is too long')
    try:
        login.decode('ascii')
    except:
        raise InvalidLogin(login=login, reason='contains invalid characters')
    for l in login:
        if not (l.islower() or l.isdigit() or l == '_'):
            raise InvalidLogin(login=login, reason='contains invalid characters')
    if not login[0].isalpha():
        raise InvalidLogin(login=login, reason='does not start with a letter')

def password_ok(password):
    if password is None:
        return
    #TODO: python-crack?
    if len(password) < 4:
        raise InvalidPassword(reason='is too short')


def sha_crypt(password, salt=None):
    if salt is None:
        chars = '0123456789abcdef'
        salt = ''
        for i in range(6):
            salt += random.choice(chars)
    hasher = hashlib.sha1()
    hasher.update(salt)
    hasher.update(password)
    return hasher.hexdigest() + salt
def sha_salt(pwhash):
    hasher = hashlib.sha1()
    return pwhash[hasher.digest_size*2:]


def password_crypt(password):
    return sha_crypt(password)

def password_check(pwhash, password):
    if pwhash is None:
        return False
    if crypt.crypt(password, pwhash) == pwhash:
    	return True
    salt = sha_salt(pwhash)
    if sha_crypt(password, salt) == pwhash:
        return True
    return False

def password_rehash_old(pwhash, password):
    if not password_check(pwhash, password):
    	return pwhash
    salt = sha_salt(pwhash)
    if sha_crypt(password, salt) == pwhash:
    	return pwhash
    return password_crypt(password)

def email_ok(email):
    if email is None:
        return
    try:
        validate_email(email)
    except ValidationError:
        raise InvalidEmail(email=email, reason='is not RFC3696 compliant')
    if len(email) > 60:
        raise InvalidEmail(email=email, reason='is too long')
