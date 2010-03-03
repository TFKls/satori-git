"""Python Hacks that deal with modules."""


import imp
import inspect
import os
import sys


__all__ = (
	'load', 'traverse', 'walk',
)


def load(qname, path=None):
	"""Loads a module by its absolute, qualified name."""
	path = path or sys.path
	qname = isinstance(qname, list) and qname or qname.split('.')
	module = sys.modules.get('.'.join(qname), None)
	if module is None:
		module = imp.new_module('(none)')
		module.__path__ = path
		for part in qname:
			module = imp.load_module(part, *imp.find_module(part, module.__path__))
	return module


def walk(root, base=[]):
	"""Generator. Walks a directory hierarchy looking for Python modules."""
	for entry in os.listdir(root):
		path = os.path.join(root, entry)
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, '__init__.py')):
			for module in walk(path, base + [entry]):
				yield module
		if not os.path.isfile(path):
			continue
		if entry[-3:] != '.py':
			continue
		if entry == '__init__.py':
			yield base
		else:
			yield base + [entry[:-3]]


def traverse(modules, topdown=True):
	"""Traverses the hierarchy of objects (modules, classes, functions and methods)."""
	def _module(module, roots, seen):
		if module not in roots:
			return
		if module in seen:
			return
		seen.add(module)
		if topdown:
			yield module
		for child in module.__dict__.itervalues():
			if inspect.ismodule(child):
				for item in _module(child, roots, seen):
					yield item
			if inspect.isclass(child):
				for item in _class(child, roots, seen):
					yield item
			if inspect.ismethod(child) or inspect.isfunction(child):
				for item in _function(child, roots, seen):
					yield item
		if not topdown:
			yield module
	def _class(class_, roots, seen):
		if sys.modules.get(class_.__module__) not in roots:
			return
		if class_ in seen:
			return
		seen.add(class_)
		if topdown:
			yield class_
		for child in class_.__dict__.itervalues():
			if inspect.isclass(child):
				for item in _class(child, roots, seen):
					yield item
			if inspect.ismethod(child) or inspect.isfunction(child):
				for item in _function(child, roots, seen):
					yield item
		if not topdown:
			yield class_
	def _function(function, roots, seen):
		if sys.modules.get(function.__module__) not in roots:
			return
		if function in seen:
			return
		seen.add(function)
		yield function		
	seen = set()
	for module in modules:
		for item in _module(module, modules, seen):
			yield item

