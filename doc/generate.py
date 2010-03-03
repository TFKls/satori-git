"""Script. Extracts information from docstrings and generates documentation."""
import sys
import os
from inspect import getsourcelines
from types import ModuleType

from apydia.descriptors import Descriptor
from apydia.generator import Generator
from apydia.project import Project
from apydia.theme import Theme

sys.path[:0] = [os.getcwd()]

from ph import modules
from ph.misc import Namespace
from ph.objects import MAGIC_SPEC, ArgumentMode
from doc import theme


class IndexDesc(Descriptor):
	"""Apydia descriptor for documentation index."""

	def __init__(self):
		Descriptor.__init__(self, None)
		self.pathname = 'modules'
		self.name = 'index'


class Options(Namespace):
	"""Options for Apydia documentation generator."""

	def __init__(self):
		super(Options, self).__init__()
		self.title = None
		self.modules = ()
		self.exclude_modules = ()
		self.destination = '.'
		self.theme = 'default'
		self.trac_browser_url = None
		self.format = 'xhtml'
		self.docformat = 'reStructuredText'


def trim(docstring):
	if not docstring:
		return ''
	# Convert tabs to spaces (following the normal Python rules) and split into lines:
	lines = docstring.expandtabs().splitlines()
	# Determine minimum indentation (first line doesn't count):
	indent = sys.maxint
	for line in lines[1:]:
		stripped = line.lstrip()
		if stripped:
			indent = min(indent, len(line) - len(stripped))
	# Remove indentation (first line is special):
	trimmed = [lines[0].strip()]
	if indent < sys.maxint:
		for line in lines[1:]:
			trimmed.append(line[indent:].rstrip())
	# Strip off trailing and leading blank lines:
	while trimmed and not trimmed[-1]:
		trimmed.pop()
	while trimmed and not trimmed[0]:
		trimmed.pop(0)
	# Return a single string:
	return '\n'.join(trimmed)


def describe(name, spec):
	return (spec.mode == ArgumentMode.PROVIDED) and "" or (name + " (" + str(spec) + ")" + "\n  " + spec.description + "\n")


def updatedoc(item):
	"""Update docstring on an item."""
	if not hasattr(item, '__doc__'):
		return
	paras = trim(item.__doc__).split('\n\n')
	if len(paras) > 1:
		paras[1:1] = ["Details\n-------"]
	if hasattr(item, 'func_dict'):
		if MAGIC_SPEC in item.func_dict:
			doc = ""
			for name, spec in item.func_dict[MAGIC_SPEC].iteritems():
				doc += describe(name, spec)
			paras[1:1] = ["Arguments:", doc]
	if hasattr(item, '__init__') and hasattr(item.__init__, 'func_dict'):
		if MAGIC_SPEC in item.__init__.func_dict:
			doc = ""
			for name, spec in item.__init__.func_dict[MAGIC_SPEC].iteritems():
				doc += describe(name, spec)
			paras[1:1] = ["Constructor Arguments\n---------------------", doc]
	try:
		item.__doc__ = '\n\n'.join(paras)
	except AttributeError:
		pass


def generate(root, revision):
	"""Collect modules and generate documentation."""
	def sourcelink(descriptor):
		"""Produce a trac browser link for a given descriptor."""
		PATTERN = "{0}href.browser('{1}', rev='{2}'){4}#L{3}"
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
			return PATTERN.format('${', path, revision, line, '}')
		except Exception:		# pylint: disable-msg=W0703
			return ''

	options = Options()
	options.destination = os.path.join(os.getcwd(), sys.argv[1])
	options.modules = list('.'.join(m) for m in modules.walk(os.getcwd()))
	options.sourcelink = sourcelink		# pylint: disable-msg=W0201

	for item in modules.traverse([modules.load(m, [os.getcwd()]) for m in options.modules], False):
		updatedoc(item)

	project = Project(options)
	project.theme = Theme('default', theme)
	project.generate()
	
	options.modules.append('')
	Generator(project).generate(IndexDesc())


if __name__ == '__main__':
	generate(os.path.abspath(os.getcwd()), sys.argv[2])

