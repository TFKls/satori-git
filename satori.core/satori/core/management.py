# vim:ts=4:sts=4:sw=4:expandtab

from django.db.models.signals import post_syncdb

def create_admin(app, created_models, verbosity, **kwargs):
    import satori.core.models
    from satori.core.models import Entity

    if (app != satori.core.models) or (Entity not in created_models):
        return

    from django.conf import settings
    from satori.core.api import ApiSecurity, ApiPrivilege
    from satori.core.sec import Token

    print 'Creating superuser'

    token = Token('')
    admin = ApiSecurity.Security_register.implementation(token, login=settings.ADMIN_NAME, fullname='Super Admin', password=settings.ADMIN_PASSWORD)
    ApiPrivilege.Privilege_global_grant.implementation(token, admin, 'ADMIN')

post_syncdb.connect(create_admin)
