from django.db.models.signals import post_syncdb

def create_admin(app, created_models, verbosity, **kwargs):
    import satori.core.models
    from satori.core.models import Object

    if (app != satori.core.models) or (Object not in created_models):
    	return

    from satori.core import settings
    from satori.core.api import ApiSecurity, ApiPrivilege
    from satori.core.sec import Token
    
    print 'Creating superuser'

    token = Token('')
    admin = ApiSecurity.Security_register.implementation(token=token, login=settings.ADMIN_NAME, fullname='Super Admin', password=settings.ADMIN_PASSWORD)
    ApiPrivilege.Privilege_create_global.implementation(token=token, role=admin, right='ADMIN')

post_syncdb.connect(create_admin)
