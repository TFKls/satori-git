import hashlib, base64

from satori.core import setup
from django.conf import settings
from django.db import models


BLOBHASH = hashlib.sha384


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
	__metaclass__ = models.SubfieldBase
	def db_type(self):
		if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
			return 'bytea'
		raise NotImplementedError
	def to_python(self, value):
		if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
			if value is None:
				return value
			return str(value)
		raise NotImplementedError
	def get_db_prep_save(self, value):
		if value is None:
			return None
		if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
			import psycopg2
			return psycopg2.Binary(value)
		raise NotImplementedError

class Blob(models.Model):
	hash		= models.CharField(max_length=(BLOBHASH().digest_size *8 +5)/6, primary_key=True)
	data		= BlobField()
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
	object		= models.ForeignKey('Object', related_name='attributes')
	name		= models.CharField(max_length=50)
	class Meta:
		unique_together = (('object','name'),)

class StringAttribute(OpenAttribute):
	value		= models.CharField(max_length=50)

class BlobAttribute(OpenAttribute):
	hash		= models.ForeignKey('Blob')

class OpaqueAttribute(OpenAttribute):
	value		= models.TextField()

class Object(models.Model):
	pass
	# attributes	(Manager created automatically by OpenAttribute)

class Problem(Object):
	name		= models.CharField(max_length=50, unique=True)
	description	= models.TextField(blank=True, default="")

class Test(Object):
	owner		= models.ForeignKey('User', null=True)
	problem		= models.ForeignKey('Problem', null=True)
	name		= models.CharField(max_length=50)
	description	= models.TextField(blank=True, default="")
	environment	= models.CharField(max_length=50)
	class Meta:
		unique_together = (('problem','name'),)

class TestSuite(Object):
	owner		= models.ForeignKey('User', null=True)
	problem		= models.ForeignKey('Problem', null=True)
	name		= models.CharField(max_length=50)
	members		= models.ManyToManyField('Test')
	dispatcher	= models.CharField(max_length=128, choices=DISPATCHERS)
	aggregator1	= models.CharField(max_length=128, choices=AGGREGATORS1)
	class Meta:
		unique_together = (('problem','name'),)

class ProblemIncarnation(Object):
	problem		= models.ForeignKey('Problem')
	description	= models.TextField()
	test_suite	= models.ForeignKey('TestSuite')
	aggregator2	= models.CharField(max_length=128, choices=AGGREGATORS2)

class Contest(Object):
	name		= models.CharField(max_length=50, unique=True)
	problems	= models.ManyToManyField('ProblemIncarnation', through='ProblemMapping')
	aggregator3	= models.CharField(max_length=128, choices=AGGREGATORS3)
	# TODO: add presentation options

class ProblemMapping(Object):
	contest		= models.ForeignKey('Contest')
	code		= models.CharField(max_length=10)
	problem		= models.ForeignKey('ProblemIncarnation')
	class Meta:
		unique_together = (('contest','code'),('contest','problem'))

class Role(Object):
	name		= models.CharField(max_length=50)
	absorbing	= models.BooleanField(default=False)

class User(Role):
	pass
	# add validation

class Contestant(Role):
	contest		= models.ForeignKey('Contest')

class Submit(Object):
	owner		= models.ForeignKey('Contestant', null=True)
	problem		= models.ForeignKey('ProblemIncarnation', null=True)
	time		= models.DateTimeField(auto_now_add=True)

class TestResult(Object):
	submit		= models.ForeignKey('Submit')
	test		= models.ForeignKey('Test')
	tester		= models.ForeignKey('User')
	class Meta:
		unique_together = (('submit','test'),)

class TestSuiteResult(Object):
	submit		= models.ForeignKey('Submit')
	test_suite	= models.ForeignKey('TestSuite')
	class Meta:
		unique_together = (('submit','test_suite'),)

class ProblemResult(Object):
	contestant	= models.ForeignKey('Contestant')
	problem		= models.ForeignKey('ProblemIncarnation')
	class Meta:
		unique_together = (('contestant','problem'),)

