# vim:ts=4:sts=4:sw=4:expandtab
"""Takes care of settings required by Django. Import this module before django.*
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.test_settings'

from django.core.management import setup_environ
from satori import test_settings

setup_environ(test_settings)

from django.db import connection
from django.core.management.color import no_style

# Get a list of already installed *models* so that references work right.
tables = connection.introspection.table_names()
seen_models = connection.introspection.installed_models(tables)
created_models = set()
pending_references = {}
style = no_style()

def setupModel(model):
    cursor = connection.cursor()
    sql, references = connection.creation.sql_create_model(model, style, seen_models)
    seen_models.add(model)
    created_models.add(model)
    for refto, refs in references.items():
        pending_references.setdefault(refto, []).extend(refs)
        if refto in seen_models:
            sql.extend(connection.creation.sql_for_pending_references(refto, style, pending_references))
    sql.extend(connection.creation.sql_for_pending_references(model, style, pending_references))
    for statement in sql:
        cursor.execute(statement)
    tables.append(connection.introspection.table_name_converter(model._meta.db_table))

