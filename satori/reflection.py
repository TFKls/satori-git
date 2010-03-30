"""Uniform view for Python reflection information.
"""


import inspect
import os
import sys
import types

from satori.objects import Object, Argument, ArgumentError, DispatchOn


class Reflector(Object, dict):
    """Caches and interrelates descriptors for reflected objects.
    """

    def __init__(self):
        self.groups = []
        self.implicit = SystemModules(cache=self)

    def __getitem__(self, obj):
        if obj not in self:
            descriptor = self._create(obj)
            self[obj] = descriptor
        return super(Reflector, self).__getitem__(obj)

    def add(self, type_, **kwargs):
        """Construct and add a descriptor of a given type.
        """
        kwargs['cache'] = self
        group = type_(**kwargs)
        self.groups.append(group)
        return group

    @DispatchOn(obj=types.ModuleType)
    def _create(self, obj):                                    # pylint: disable-msg=E0102
        return Module(obj=obj, cache=self)

    @DispatchOn(obj=types.ClassType)
    @DispatchOn(obj=types.TypeType)
    def _create(self, obj):                                    # pylint: disable-msg=E0102
        return Class(obj=obj, cache=self)

    @DispatchOn(obj=types.MethodType)
    def _create(self, obj):                                    # pylint: disable-msg=E0102
        return Method(obj=obj, cache=self)

    @DispatchOn(obj=types.FunctionType)
    def _create(self, obj):                                    # pylint: disable-msg=E0102
        return Function(obj=obj, cache=self)

    def __iter__(self):
        seen = set()
        for group in self.groups:
            for descendant in group.traverse(seen):
                yield descendant


_ismodule = lambda p: isinstance(p[1], Module)
_isclass = lambda p: isinstance(p[1], Class) and not p[0].startswith('_')
_ismethod = lambda p: isinstance(p[1], Method) and not p[0].startswith('_')
_isfunction = lambda p: isinstance(p[1], Function) and not p[0].startswith('_')


class Descriptor(Object):
    """Base class for descriptors of reflected objects.
    """

    @Argument('cache', type=Reflector)
    def __init__(self, obj, cache):
        self.object = obj
        self.cache = cache
        self.name = getattr(self.object, '__name__', None)
        self.docstring = inspect.cleandoc(getattr(self.object, '__doc__', None) or "")

    class source_file(object):                                 # pylint: disable-msg=C0103
        """Lazy property. The path of the source file for the described object.
        """
        def __get__(_, self, _type=None):                      # pylint: disable-msg=E0213
            try:
                self.source_file = os.path.abspath(inspect.getsourcefile(self.object))
                return self.source_file
            except:                                            # pylint: disable-msg=W0702
                return None
    source_file = source_file()

    class source_line(object):                                 # pylint: disable-msg=C0103
        """Lazy property. The number of the first source line for the described object.
        """
        def __get__(_, self, _type=None):                      # pylint: disable-msg=E0213
            try:
                lines = inspect.getsourcelines(self.object)
                self.source_code = '\n'.join(lines[0])
                self.source_line = lines[1] or 1
                return self.source_line
            except:                                            # pylint: disable-msg=W0702
                return None
    source_line = source_line()

    class source_code(object):                                 # pylint: disable-msg=C0103
        """Lazy property. The source code for the described object.
        """
        def __get__(_, self, _type=None):                      # pylint: disable-msg=E0213
            try:
                lines = inspect.getsourcelines(self.object)
                self.source_code = '\n'.join(lines[0])
                self.source_line = lines[1] or 1
                return self.source_code
            except:                                            # pylint: disable-msg=W0702
                return None
    source_code = source_code()

    @property
    def children(self):
        """Generator. Enumerate this descriptor's children.
        """
        for name in dir(self.object):
            try:
                obj = getattr(self.object, name)
                yield name, self.cache[obj]
            except (AttributeError, KeyError, TypeError, ArgumentError):
                pass

    modules = property(lambda self: (x for x in self.children if _ismodule(x)))
    classes = property(lambda self: (x for x in self.children if _isclass(x)))
    methods = property(lambda self: (x for x in self.children if _ismethod(x)))
    functions = property(lambda self: (x for x in self.children if _isfunction(x)))

    def traverse(self, seen=None):
        """Generator. Enumerate this descriptor's descendants.
        """
        seen = seen or set()
        if self in seen:
            return
        seen.add(self)
        yield self
        for _, child in self.children:
            for descendant in child.traverse(seen):
                yield descendant


class ModuleGroup(Descriptor):
    """A Descriptor for a group of modules.
    """

    @Argument('obj', fixed=None)
    def __init__(self):
        self.module_list = []
        self.parent = self
        self.group = self

    @property
    def children(self):
        """Generator. Enumerate this descriptor's children.
        """
        by_name = lambda m1, m2: cmp(m1.__name__, m2.__name__)
        for module in sorted(self.module_list, by_name):
            yield module.__name__, self.cache[module]

    def __contains__(self, module):
        return module in self.module_list


class SystemModules(ModuleGroup):
    """A Descriptor for system modules.
    """

    def __contains__(self, module):
        return True

    def __str__(self):
        return "(system modules)"


class Location(ModuleGroup):
    """A Descriptor for module group defined in a single place.
    """

    @Argument('root', type=str)
    def __init__(self, root):

        def walk(root, base=[]):                               # pylint: disable-msg=W0102
            """Generator. Walk a directory hierarchy looking for Python modules.
            """
            for entry in os.listdir(root):
                path = os.path.join(root, entry)
                if os.path.isdir(path):
                    if os.path.isfile(os.path.join(path, '__init__.py')):
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

        self.root = root
        sys.path.insert(0, self.root)
        for parts in walk(self.root):
            name = '.'.join(parts)
            __import__(name)
            self.module_list.append(sys.modules[name])
        sys.path.remove(self.root)

    def __str__(self):
        return self.root


class Module(Descriptor):
    """A Descriptor for a module.
    """

    def __init__(self):
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
        """Generator. Enumerate this descriptor's children.
        """
        for name, child in super(Module, self).children:
            if child.parent is self:
                yield name, child

    def __str__(self):
        return "module {0} at {1}".format(self.name, self.group)


class Class(Descriptor):
    """A Descriptor for a class.
    """

    def __init__(self):
        self.parent = self.cache[sys.modules[self.object.__module__]]
        self.group = self.parent.group
        self.bases = [self.cache[base] for base in self.object.__bases__]

    def __str__(self):
        return "class {0} in {1}".format(self.name, self.parent)


class Callable(Descriptor):
    """A Descriptor for a callable.
    """

    def __init__(self):
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
        """Generator. Enumerate this descriptor's children.
        """
        return []

    def __str__(self):
        return "{0}({1}) in {2}".format(self.name, self.signature, self.parent)


class Method(Callable):
    """A Descriptor for a method.
    """

    def __init__(self):
        class_ = self.object.im_class
        code = self.object.func_code
        for base in class_.__mro__:
            if hasattr(base, self.name):
                impl = getattr(base, self.name, None)
                if getattr(impl, 'func_code', None) is code:
                    class_ = base
        self.parent = self.cache[class_]
        self.group = self.parent.group


class Function(Callable):
    """A Descriptor for a function.
    """

    def __init__(self):
        self.parent = self.cache[sys.modules[self.object.__module__]]
        self.group = self.parent.group
