# vim:ts=4:sts=4:sw=4:expandtab

import os
import shutil

from django.db.models.signals import post_syncdb

def create_admin(app, created_models, verbosity, **kwargs):
    import satori.core.models
    from satori.core.models import Entity

    if (app != satori.core.models) or (Entity not in created_models):
        return

    from django.conf import settings
    from django.db   import connection, transaction

    from satori.core.dbev.install import install_dbev_sql, install_rights_sql
    from satori.core.export       import token_container, DjangoStruct
    from satori.core.models       import Security, Privilege, Global, User, Machine
    from satori.core.sec          import Token

    print 'Installing DBEV'

    sql = install_dbev_sql()
    cursor = connection.cursor()
    for query in sql:
    	cursor.execute(query)
    cursor.close()

    print 'Creating Global object'
    Global.create()

    print 'Installing DBEV rights'

    sql = install_rights_sql()
    from django.db import connection, transaction
    cursor = connection.cursor()
    for query in sql:
    	cursor.execute(query)
    cursor.close()

    print 'Creating superuser'

    token_container.set_token(Token(''))
    admin = User.create(DjangoStruct('User')(login=settings.ADMIN_NAME, name='Super Admin', activated=True))
    admin.set_password(settings.ADMIN_PASSWORD)
    Privilege.global_grant(admin, 'ADMIN')

    print 'Creating checkers'

    for (login, password, address, netmask) in settings.CHECKERS:
        checker = Machine.create(DjangoStruct('Machine')(login=login, address=address, netmask=netmask))
        checker.set_password(password)
        Privilege.global_grant(checker, 'JUDGE')

    print 'Registering default judge'
    
    default_judge_src = os.path.join(os.path.split(__file__)[0], '..', 'default_judge.py')
    blob = Global.get_instance().judges_set_blob('default_judge', 'judge.py')
    with open(default_judge_src) as default_judge:
        shutil.copyfileobj(default_judge, blob)
    blob.close()

    print 'Setting default profile fields'
    profile_xml = """
<profile>
  <input>
    <param name="affiliation" description="Affiliation" type="text" required="true"/>
  </input>
</profile>
"""
    Global.get_instance().profile_fields = profile_xml

post_syncdb.connect(create_admin)
