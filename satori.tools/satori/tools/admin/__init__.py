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
    #u.set_password(opts.pwd)
