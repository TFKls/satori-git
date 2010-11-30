# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Problem(Entity):
    """Model. Description of an (abstract) problems.
    """
    
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_problem')

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    statement = models.TextField(blank=True, default="")

    generate_attribute_group('Problem', 'default_test_data', 'VIEW', 'MANAGE', globals(), locals())

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('description', 'VIEW'), ('statement', 'VIEW')]

    def save(self):
        self.fixup_default_test_data()
        super(Problem, self).save()

    def __str__(self):
        return self.name+" ("+self.description+")"

    @classmethod
    def inherit_rights(cls):
        inherits = super(Problem, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', '', 'MANAGE_PROBLEMS')
        return inherits

    @ExportMethod(DjangoId('Problem'), [unicode], PCAnd(PCTokenIsUser(), PCGlobal('MANAGE_PROBLEMS')))
    def create_problem(name):
        o = Problem()
        o.name = name
        o.save()
        Privilege.grant(token_container.token.user, o, 'MANAGE')
        return o

class ProblemEvents(Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []
    
