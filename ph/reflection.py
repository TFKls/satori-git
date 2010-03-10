import inspect
import os
import sys
import types

from ph.objects import Object, Argument
from ph.patterns import visitor


class Reflector(Object, dict):

	def __init__(self, kwargs):
		self.groups = []
		self.implicit = SystemModules(cache=self)

	def __getitem__(self, object):
		if object not in self:
			descriptor = self._create(object)
			self[object] = descriptor
		return super(Reflector, self).__getitem__(object)
	
	def add(self, type, **kwargs):
		kwargs['cache'] = self
		group = type(**kwargs)
		self.groups.append(group)
		return group
	
	@visitor.Dispatch(argument=1)
	def _create(self, object):
		raise KeyError("Unhandled object type '{0}'".format(object.__class__))

	@visitor.Implement(type=types.ModuleType)
	def _create(self, object):
		return Module(object=object, cache=self)

	@visitor.Implement(type=(types.ClassType, types.TypeType))
	def _create(self, object):
		return Class(object=object, cache=self)

	@visitor.Implement(type=types.MethodType)
	def _create(self, object):
		return Method(object=object, cache=self)

	@visitor.Implement(type=types.FunctionType)
	def _create(self, object):
		return Function(object=object, cache=self)

	def __iter__(self):
		seen = set()
		for group in self.groups:
			for descendant in group.traverse(seen):
				yield descendant
	

class Descriptor(Object):

	@Argument('object')
	@Argument('cache', type=Reflector)
	def __init__(self, kwargs):
		self.object = kwargs.object
		self.cache = kwargs.cache
		self.name = getattr(self.object, '__name__', None)
		self.docstring = getattr(self.object, '__doc__', None)

	class source_file(object):
		def __get__(_, self, type=None):
			try:
				self.source_file = inspect.getsourcefile(self.object)
				return self.source_file
			except:
				return None
	source_file = source_file()

	class source_line(object):
		def __get__(_, self, type=None):
			try:
				lines = inspect.getsourcelines(self.object)
				self.source_code = '\n'.join(lines[0])
				self.source_line = lines[1] or 1
				return self.source_line
			except:
				return None
	source_line = source_line()

	class source_code(object):
		def __get__(_, self, type=None):
			try:
				lines = inspect.getsourcelines(self.object)
				self.source_code = '\n'.join(lines[0])
				self.source_line = lines[1] or 1
				return self.source_code
			except:
				return None
	source_code = source_code()

	@property
	def children(self):
		for name in dir(self.object):
			try:
				object = getattr(self.object, name)
				yield name, self.cache[object]
			except (AttributeError, KeyError, TypeError) as ex:
				pass

	def traverse(self, seen=None):
		seen = seen or set()
		if self in seen:
			return
		seen.add(self)
		yield self
		for name, child in self.children:
			for descendant in child.traverse(seen):
				yield descendant


class ModuleGroup(Descriptor):
	
	@Argument('object', fixed=None)
	def __init__(self, kwargs):
		self.module_list = []
		self.group = self
		pass
	
	@property
	def children(self):
		for module in self.module_list:
			yield module.__name__, self.cache[module]
	
	def __contains__(self, module):
		return module in self.module_list


class SystemModules(ModuleGroup):

	def __contains__(self, module):
		return True

	def __str__(self):
		return "(system modules)"


class Location(ModuleGroup):

	@Argument('root', type=str)
	def __init__(self, kwargs):

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

		self.root = kwargs.root
		sys.path.insert(0, self.root)
		for parts in walk(self.root):
			name = '.'.join(parts)
			__import__(name)
			self.module_list.append(sys.modules[name])
		sys.path.remove(self.root)

	def __str__(self):
		return self.root


class Module(Descriptor):

	def __init__(self, kwargs):
		self.group = None
		for group in self.cache.groups:
			if self.object in group:
				self.group = group
		if self.name.count('.'):
			parent = sys.modules[self.name[:self.name.rfind('.')]]
			self.parent = self.cache[parent]
			self.group = self.group or self.parent.group
		else:
			self.group = self.group or self.cache.implicit
			self.parent = self.group

	@property
	def children(self):
		for name, child in super(Module, self).children:
			if child.parent is self:
				yield name, child
	
	def __str__(self):
		return "module {0} at {1}".format(self.name, self.group)


class Class(Descriptor):

	def __init__(self, kwargs):
		self.parent = self.cache[sys.modules[self.object.__module__]]
		self.bases = [self.cache[base] for base in self.object.__bases__]

	def __str__(self):
		return "class {0} in {1}".format(self.name, self.parent)


class Callable(Descriptor):

	def __init__(self, kwargs):
		spec = inspect.getargspec(self.object)
		args = spec.args
		defs = spec.defaults or ()
		sign = []
		for index, name in enumerate(args):
			if len(args) - index <= len(defs):
				sign.append(name + '=' + str(defs[index-len(args)]))
			else:
				sign.append(name)
		if spec.varargs is not None:
			sign.append('*' + spec.varargs)
		if spec.keywords is not None:
			sign.append('**' + spec.keywords)
		self.signature = ', '.join(sign)

	@property
	def children(self):
		return []

	def __str__(self):
		return "{0}({1}) in {2}".format(self.name, self.signature, self.parent)


class Method(Callable):

	def __init__(self, kwargs):
		class_ = self.object.im_class
		code = self.object.func_code
		for base in class_.__mro__:
			if hasattr(base, self.name):
				impl = getattr(base, self.name, None)
				if getattr(impl, 'func_code', None) is code:
					class_ = base
		self.parent = self.cache[class_]


class Function(Callable):

	def __init__(self, kwargs):
		self.parent = self.cache[sys.modules[self.object.__module__]]
