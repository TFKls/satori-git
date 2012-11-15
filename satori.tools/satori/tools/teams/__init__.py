# vim:ts=4:sts=4:sw=4:expandtab

import logging
import os
import shutil
import sys

from satori.client.common import want_import
from satori.tools import config, options, setup, auth_setup, catch_exceptions
want_import(globals(), '*')

@catch_exceptions
def uzi_team():
    options.add_argument('contest', help='contest_name')
    options.add_argument('team', help='team_name')
    options.add_argument('contestants', nargs='+', metavar='contestant', help='contest name')
    opts = setup(logging.CRITICAL)

    contest_name=opts.contest
    name=opts.team
    users_name=opts.contestants

    c=Contest.filter(ContestStruct(name=contest_name))
    if len(c) >= 1:
    	contest=c[0]
    else:
        logging.error('incorrect contest name '+contest_name)
        sys.exit(1)

    users = set()
    for un in users_name:
        u=User.filter(UserStruct(login=un, activated=True))
        if len(u) > 1:
            raise RuntimeError("To many matches for '" + un + "'")
        elif len(u) == 1:
        	users.add(u[0]);
        else:
            u=User.filter(UserStruct(name=un, activated=True))
            if len(u) > 1:
                raise RuntimeError("To many matches for '" + un + "'")
            if len(u) == 1:
                users.add(u[0]);
            else:
                raise RuntimeError('Unknown user name '+un)

    users = list(users)
    if not len(users) :
        raise RuntimeError('no users')

    print contest.name, name,[user.name for user in users],users
    Contestant.create(fields=ContestantStruct(contest=contest,name=name,accepted=True), user_list=users)
