"""Database schema for satori.core.
"""


import hashlib, base64

import satori.core.setup                                       # pylint: disable-msg=W0611
from django.conf import settings
from django.db import models
from satori.dbev import events

BLOBHASH = hashlib.sha384
HASHSIZE = (BLOBHASH().digest_size * 8 + 5) / 6


# built-in script identifiers
DISPATCHERS = (
    ('fully.qualified.Name','description'),
)
AGGREGATORS1 = (
    ('fully.qualified.Name','description'),
)
AGGREGATORS2 = (
    ('fully.qualified.Name','description'),
)
AGGREGATORS3 = (
    ('fully.qualified.Name','description'),
)


class BlobField(models.Field):
    """A django Field for BLOBs (Binary Large OBjects).

    Currently works only with postgresql_psycopg2 engine.
    """

    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):                            # pylint: disable-msg=C0103
        """Return the database column type for this Field.
        """
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            return 'bytea'
        raise NotImplementedError

    def to_python(self, value):                                # pylint: disable-msg=C0103
        """Convert a value from database to Python format.
        """
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            if value is None:
                return value
            return str(value)
        raise NotImplementedError

    def get_db_prep_save(self, value, _connection):            # pylint: disable-msg=C0103
        """Convert a value from Python to database format.
        """
        if value is None:
            return None
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            import psycopg2
            return psycopg2.Binary(value)
        raise NotImplementedError


# pylint: disable-msg=W0232

class Blob(models.Model):
    """Model. BLOB, keyed by content digest.
    """

    hash        = models.CharField(max_length=HASHSIZE, primary_key=True)
    data        = BlobField()

    def __setattr__(self, name, value):
        if name == 'hash':
            return
        models.Model.__setattr__(self, name, value)
        if name == 'data':
            if self.data is None:
                self.__dict__['hash'] = None
            else:
                self.__dict__['hash'] = base64.b64encode(BLOBHASH(self.data).digest())


class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """

    object      = models.ForeignKey('Object', related_name='attributes')
    name        = models.CharField(max_length=50)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)


class StringAttribute(OpenAttribute):
    """Model. Open attribute of kind "string".
    """

    value       = models.CharField(max_length=50)


class BlobAttribute(OpenAttribute):
    """Model. Open attribute of kind "blob".
    """

    hash        = models.ForeignKey('Blob')


class OpaqueAttribute(OpenAttribute):
    """Model. Open attribute of kind "opaque".
    """

    value       = models.TextField()


class Object(models.Model):
    """Model. Base for all database objects. Provides common GUID space.
    """

    pass
    # attributes    (Manager created automatically by OpenAttribute)


class Problem(Object):
    """Model. Description of an (abstract) problems.
    """

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
class ProblemEvents(events.Events):
    model = Problem
    on_insert = on_update = ('name')
    on_delete = ()


class Test(Object):
    """Model. Single test.
    """

    owner       = models.ForeignKey('User', null=True)
    problem     = models.ForeignKey('Problem', null=True)
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    environment = models.CharField(max_length=50)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)
class TestEvents(events.Events):
    model = Test
    on_insert = on_update = ('owner', 'problem', 'name')
    on_delete = ()


class TestSuite(Object):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """

    owner       = models.ForeignKey('User', null=True)
    problem     = models.ForeignKey('Problem', null=True)
    name        = models.CharField(max_length=50)
    members     = models.ManyToManyField('Test')
    dispatcher  = models.CharField(max_length=128, choices=DISPATCHERS)
    aggregator1 = models.CharField(max_length=128, choices=AGGREGATORS1)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)
class TestSuiteEvents(events.Events):
    model = TestSuite
    on_insert = on_update = ('owner', 'problem', 'name')
    on_delete = ()


class ProblemIncarnation(Object):
    """Model. Specific version of a Problems, as used in (one or more) Contests.
    """

    problem     = models.ForeignKey('Problem')
    description = models.TextField()
    test_suite  = models.ForeignKey('TestSuite')
    aggregator2 = models.CharField(max_length=128, choices=AGGREGATORS2)
class ProblemIncarnationEvents(events.Events):
    model = ProblemIncarnation
    on_insert = on_update = ('problem', 'test_suite')
    on_delete = ()

class Contest(Object):
    """Model. Description of a contest.
    """

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('ProblemIncarnation', through='ProblemMapping')
    aggregator3 = models.CharField(max_length=128, choices=AGGREGATORS3)
    # TODO: add presentation options
class ContestEvents(events.Events):
    model = Contest
    on_insert = on_update = ('name')
    on_delete = ()


class ProblemMapping(Object):
    """Model. Intermediary for many-to-many relationship between Contests and
    ProblemIncarnations.
    """

    contest     = models.ForeignKey('Contest')
    code        = models.CharField(max_length=10)
    problem     = models.ForeignKey('ProblemIncarnation')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))
class ProblemMappingEvents(events.Events):
    model = ProblemMapping
    on_insert = on_update = ('contest', 'problem')
    on_delete = ()


class Role(Object):
    """Model. Base for authorization "levels".
    """

    name        = models.CharField(max_length=50)
    absorbing   = models.BooleanField(default=False)
class RoleEvents(events.Events):
    model = Role
    on_insert = on_update = ('name')
    on_delete = ()


class User(Role):
    """Model. A Role which can be logged onto.
    """

    pass
    # add validation
class UserEvents(events.Events):
    model = User
    on_insert = on_update = ('name')
    on_delete = ()


class Contestant(Role):
    """Model. A Role for a contest participant.
    """

    contest     = models.ForeignKey('Contest')
class ContestantEvents(events.Events):
    model = Contestant
    on_insert = on_update = ('name', 'contest')
    on_delete = ()


class Submit(Object):
    """Model. Single problem solution (within or outside of a Contest).
    """

    owner       = models.ForeignKey('Contestant', null=True)
    problem     = models.ForeignKey('ProblemIncarnation', null=True)
    time        = models.DateTimeField(auto_now_add=True)
class SubmitEvents(events.Events):
    model = Submit
    on_insert = on_update = ('owner', 'problem')
    on_delete = ()


class TestResult(Object):
    """Model. Result of a single Test for a single Submit.
    """

    submit      = models.ForeignKey('Submit')
    test        = models.ForeignKey('Test')
    tester      = models.ForeignKey('User')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test'),)
class TestResultEvents(events.Events):
    model = TestResult
    on_insert = on_update = ('submit', 'test', 'tester')
    on_delete = ()


class TestSuiteResult(Object):
    """Model. Result of a TestSuite for a single Submit.
    """

    submit      = models.ForeignKey('Submit')
    test_suite  = models.ForeignKey('TestSuite')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test_suite'),)
class TestSuiteResultEvents(events.Events):
    model = TestSuiteResult
    on_insert = on_update = ('submit', 'test_suite')
    on_delete = ()


class ProblemResult(Object):
    """Model. Cumulative result of all submits of a particular ProblemIncarnation by
    a single Contestant.
    """

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemIncarnation')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contestant', 'problem'),)
class ProblemResultEvents(events.Events):
    model = ProblemResult
    on_insert = on_update = ('contestant', 'problem')
    on_delete = ()


# pylint: enable-msg=W0232
