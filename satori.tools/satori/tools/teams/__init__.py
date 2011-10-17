# vim:ts=4:sts=4:sw=4:expandtab

import logging
import os
import shutil
import sys

from satori.client.common import want_import
want_import(globals(), '*')

def uzi_team():
    from satori.tools import options, setup
    (options, args) = setup()

    contest_name=args[0]
    name=args[1]
    users_name=args[2:]

    c=Contest.filter(ContestStruct(name=contest_name))
    if len(c) >= 1:
    	contest=c[0]
    else:
        logging.error('incorrect contest name '+contest_name)
        sys.exit(1)

    users = list()
    for un in users_name:
    	u=User.filter(UserStruct(name=un))
        if len(u) >= 1:
        	users.append(u[0]);
        else:
            u=User.filter(UserStruct(login=un))
            if len(u) >= 1:
                users.append(u[0]);
            else:
                logging.error('incorrect user name '+un)
                sys.exit(1)
    if not len(users) :
                logging.error('no users')
                sys.exit(1)

    print contest.name, name,[user.name for user in users],users
    Contestant.create(fields=ContestantStruct(contest=contest,name=name,accepted=True), user_list=users)
