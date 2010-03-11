"""
Script. Extracts information from docstrings and generates documentation.
"""


import sys
import os

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import genshi.template
import pygments.token

from doc import sourcecode
from ph.misc import Namespace
from ph.objects import Object, Argument
from ph.patterns import visitor
from ph.reflection import Reflector, Location, Module, Class, Method, Function


class Generator(Reflector):

	@Argument('template_dir', type=str)
	def __init__(self, kwargs):
		self.templates = genshi.template.TemplateLoader(kwargs.template_dir, variable_lookup='lenient')
		self.docutils_parser = docutils.parsers.rst.Parser()
		self.docutils_settings = dict(
			pep_references=False,
			rfc_references=True,
			tab_width=4,
			trim_footnote_reference_space=True,
		)
		self.data = Namespace()

	def parseDocstring(self, desc):
		options = docutils.frontend.OptionParser()
		options.set_defaults_from_dict(self.docutils_settings)
		desc.doc = docutils.utils.new_document(desc.name, settings=options.get_default_values())
		self.docutils_parser.parse(desc.docstring or "(not documented)", desc.doc)
		desc.doc.transformer.apply_transforms()
		ispara = lambda node: isinstance(node, docutils.nodes.paragraph)
		desc.shortdoc = filter(ispara, desc.doc.traverse())[0]

	@visitor.Dispatch(argument=1)
	def update(self, desc):
		pass

	@visitor.Implement(type=Location)
	def update(self, desc):
		desc.template = 'index.html'
		desc.target_path = os.path.join(desc.target_dir, 'index.html')

	@visitor.Implement(type=Module)
	def update(self, desc):
		if isinstance(desc.group, Location):
			desc.template = 'module.html'
			desc.target_path = os.path.join(desc.group.target_dir, desc.name+'.html')
		self.parseDocstring(desc)
		desc.doc.insert(0, docutils.nodes.title(text=desc.name))

	@visitor.Implement(type=Class)
	def update(self, desc):
		if isinstance(desc.group, Location):
			desc.template = 'class.html'
			desc.target_path = os.path.join(desc.group.target_dir, desc.parent.name+'.'+desc.name+'.html')
		self.parseDocstring(desc)
		desc.doc.insert(0, docutils.nodes.title(text=desc.parent.name+'.'+desc.name))

	@visitor.Implement(type=(Function, Method))
	def update(self, desc):
		self.parseDocstring(desc)

	def run(self):
		# first pass: resolve references
		for desc in self:
			pass
		# second pass: update descriptor data
		for desc in self:
			self.update(desc)
		# third pass: generate output
		for desc in self:
			if not hasattr(desc, 'template'):
				continue
			template = self.templates.load(desc.template)
			with open(desc.target_path, 'w') as output:
				self.data.this = desc
				output.write(template.generate(**self.data).render('xhtml'))


if __name__ == '__main__':
	target_dir = sys.argv[1]
	revision = sys.argv[2]
	template_dir = os.path.join(os.path.dirname(sys.argv[0]), 'templates')
	if not os.path.isdir(target_dir):
		os.mkdir(target_dir)
	generator = Generator(template_dir=template_dir)
	generator.data.pygments = pygments.token.STANDARD_TYPES
	location = generator.add(Location, root=os.getcwd())
	location.target_dir = target_dir.rstrip('/') + '/'
	location.target_url = lambda path: "{0}href.api('{1}'){2}".format('${', path, '}')
	location.source_url = lambda path: "{0}href.browser('{1}', rev={2}){3}".format('${', path, revision, '}')
	generator.run()
