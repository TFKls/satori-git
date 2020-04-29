# vim:ts=4:sts=4:sw=4:expandtab

import logging
import os
import shutil
import sys

from satori.client.common import want_import
from satori.tools import config, options, setup, auth_setup, catch_exceptions
want_import(globals(), '*')

@catch_exceptions
def passwd():
    options.add_argument('usr', help='username')
    options.add_argument('pwd', help='password')
    opts = setup(logging.INFO)
    u=User.filter(UserStruct(login=opts.usr))[0]
    logging.info("Changing password for user %s"%(u.name,))
    u.set_password(opts.pwd)

@catch_exceptions
def addchecker():
    options.add_argument('login', help='login')
    options.add_argument('address', help='address')
    options.add_argument('pwd', help='password')
    opts = setup(logging.INFO)
    m=Machine.create(MachineStruct(login=opts.login, address=opts.address, netmask='255.255.255.255'))
    m.set_password(opts.pwd)
    Privilege.global_grant(m, 'JUDGE')

@catch_exceptions
def adduser():
    options.add_argument('usr', help='username')
    options.add_argument('first', help='firstname')
    options.add_argument('last', help='lastname')
    options.add_argument('email', help='e-mail')
    options.add_argument('affiliation', help='affiliation')
    opts = setup(logging.INFO)
    u=User.create(UserStruct(login=opts.usr, firstname=opts.first, lastname=opts.last, email=opts.email, confirmed=True, activated=True, affiliation=opts.affiliation))
    logging.info("Created user %s"%(u.name,))
