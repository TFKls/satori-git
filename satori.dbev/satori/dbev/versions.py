# vim:ts=4:sts=4:sw=4:expandtab
import copy
import satori.core.setup                                       # pylint: disable-msg=W0611
from django.db import models
import satori.dbev.models
from django.db import connection

def install_versions_sql(model):
    qn = connection.ops.quote_name
    qv = lambda x : '\''+str(x)+'\''
    tabs = []
    keys = []
    mod = model
    while issubclass(mod, models.Model):
        tabs.append(str(mod._meta.db_table))
        keys.append(str(mod._meta.pk.column))
        if len(mod._meta.parents.items()) > 0:
            mod = mod._meta.parents.items()[0][0]
        else:
            break

    modify_original = """
        SELECT install_versions({0}, {1}, {2}, {3}, 'satori');
    """.format(
        qv(model._meta.db_table),
        qv(model._meta.pk.column),
        'ARRAY[' + ','.join([qv(tab) for tab in tabs]) + ']',
        'ARRAY[' + ','.join([qv(key) for key in keys]) + ']',
    )
   
    return (modify_original,)




class UserField(models.IntegerField):
    def __init__(self):
        super(UserField, self).__init__(self, blank = True, null = True)

    def post_create_sql(self, style, db_table):
        return install_versions_sql(self._model._original)



class Versions:
    def __init__(self, model, events):
        class PMeta(models.base.ModelBase):
            def __new__(cls, name, bases, attrs):
                return type.__new__(cls, name, bases, attrs)
        
        fields = {}
        fields['__module__'] = model.__module__

        fields['_version_user'] = UserField()
        class Meta(object):
            db_table = model._meta.db_table + '__versions'
        fields['Meta'] = Meta
        modelclass = models.base.ModelBase.__new__(PMeta, model.__name__+"Versions", (models.Model,), fields)
        modelclass._original = model
        for field in modelclass._meta.fields:
            field._model = modelclass

def setUserId(uid):
    connection.cursor().execute('SELECT set_user_id(%s);', [str(int(uid))])

def unsetUserId():
    connection.cursor().execute('SELECT set_user_id(NULL);')
