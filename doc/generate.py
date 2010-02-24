"""Script. Extracts information from docstrings and generates documentation."""
import sys
import os
from inspect import getsourcelines
from types import ModuleType

from apydia.descriptors import Descriptor, ModuleDesc
from apydia.generator import Generator
from apydia.project import Project
from apydia.theme import Theme

sys.path[:0] = [os.getcwd()]

from doc import theme


def enumerate_modules(root, exclude=[], prefix=''):
	"""Enumerates the names of all packages and modules under a given path."""

	for entry in os.listdir(root):
		path = os.path.join(root, entry)
		if os.path.isdir(path):
			package = prefix + entry
			if package in exclude:
				continue
			if not os.path.exists(os.path.join(path, '__init__.py')):
				continue
			for module in enumerate_modules(path, exclude=exclude, prefix=package+'.'):
				yield module
		if not os.path.isfile(path):
			continue
		if entry[-3:] != '.py':
			continue
		entry = entry[:-3]
		if entry == '__init__':
			yield prefix[:-1]
			continue
		module = prefix+entry
		if module in exclude:
			continue
		yield module


class IndexDesc(Descriptor):
	"""Apydia descriptor for documentation index."""

	def __init__(self):
		Descriptor.__init__(self, None)
		self.pathname = 'modules'
		self.name = 'index'


class Options(dict):
	"""Options for Apydia documentation generator."""

	def __init__(self):
		dict.__init__(self)
		self.title = None
		self.modules = ()
		self.exclude_modules = ()
		self.destination = '.'
		self.theme = 'default'
		self.trac_browser_url = None
		self.format = 'xhtml'
		self.docformat = 'reStructuredText'

	def __getattr__(self, name):
		return self[name]

	def __setattr__(self, name, value):
		self[name] = value


if __name__ == '__main__':
	# prepare helper function
	root = os.path.abspath(os.getcwd())
	revision = sys.argv[2]
	def sourcelink(descriptor):
		try:
			obj = descriptor.value
			if isinstance(obj, ModuleType):
				module = obj
				line = 1
			else:
				module = sys.modules[obj.__module__]
				line = getsourcelines(obj)[1]
			path = module.__file__
			if path[:len(root)] != root:
				return ''
			path = path[len(root):]
			if path[-4:] in ('.pyc', '.pyo'):
				path = path[:-1]
			if path[0] == '/':
				path = path[1:]
			return "{0}href.browser('{1}', rev='{2}'){4}#L{3}".format('${', path, revision, line, '}')
		except Exception as ex:
			print ex
			return ''

	# set options
	options = Options()
	options.revision = sys.argv[2]
	options.destination = os.path.join(os.getcwd(), sys.argv[1])
	options.modules = list(enumerate_modules(os.getcwd(), exclude=['doc']))
	options.sourcelink = sourcelink

	# generate documentation
	project = Project(options)
	project.theme = Theme('default', theme)
	project.generate()

	# create module index file
	options.modules.append('')
	Generator(project).generate(IndexDesc())
