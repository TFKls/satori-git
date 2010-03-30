"""Useful additions to the standard Python class hierarchy.
"""


__all__ = (
    'Object', 'Argument', 'ArgumentMode', 'ArgumentError',
)


import inspect
import sys
import types


MAGIC_ORG = 'objects/original'
MAGIC_SIG = 'objects/signature'
MAGIC_DIS = 'objects.DispatchOn/argument name'
MAGIC_MAP = 'objects.DispatchOn/type map'


class ArgumentError(Exception):
    """Exception. A problem with an argument's specification or value.
    """

    pass


class TypeSpec(object):
    """An argument type specification."""

    def __init__(self, **kwargs):
        self.type = kwargs.get('type', [])
        self.none = kwargs.get('none', len(self.type) == 0)

    def __and__(self, other):
        type_ = self.type + other.type
        none = self.none and other.none
        return TypeSpec(type=type_, none=none)

    def __str__(self):
        desc = ""
        for type_ in self.type:
            if isinstance(type_, tuple):
                for option in type_:
                    desc += option.__name__
                    desc += " or "
                desc = desc[:-4]
            else:
                desc += type_.__name__
            desc += ", "
        if not self.none:
            desc += "not None, "
        desc = desc[:-2]
        return desc

    def isValid(self, value):
        """Checks whether a given value meets this TypeSpec."""
        if value is None:
            return self.none
        for type_ in self.type:
            if not isinstance(value, type_):
                return False
        return True


class ArgumentMode(object):
    """Enumeration. Modes for function arguments."""

    REQUIRED = 0
    OPTIONAL = 1
    PROVIDED = 2


class ValueSpec(object):
    """An argument value specification."""

    def __init__(self, **kwargs):
        self.value = None
        self.mode = ArgumentMode.REQUIRED
        if 'default' in kwargs:
            self.value = kwargs['default']
            self.mode = ArgumentMode.OPTIONAL
        if 'fixed' in kwargs:
            self.value = kwargs['fixed']
            self.mode = ArgumentMode.PROVIDED

    def __str__(self):
        if self.mode == ArgumentMode.REQUIRED:
            return "required"
        if self.mode == ArgumentMode.OPTIONAL:
            return "optional, default = " + str(self.value)
        if self.mode == ArgumentMode.PROVIDED:
            return "fixed, value = " + str(self.value)
        raise Exception('this should NOT happen!')

    def __add__(self, other):
        # one without a value always looses...
        if (self.mode == ArgumentMode.REQUIRED):
            return other
        if (other.mode == ArgumentMode.REQUIRED):
            return self
        # ...two strongmen agree or die...
        if (self.mode == ArgumentMode.PROVIDED) and (other.mode == ArgumentMode.PROVIDED):
            if self.value != other.value:
                raise ArgumentError("Conflicting provided values.")
        # ...otherwise the left has advantage
        if (other.mode == ArgumentMode.PROVIDED):
            return other
        else:
            return self

    def __and__(self, tspec):
        if self.mode == ArgumentMode.REQUIRED:
            return self
        if tspec.isValid(self.value):
            return self
        if self.mode == ArgumentMode.OPTIONAL:
            return ValueSpec()
        else:
            raise TypeError("'{0}' does not satisfy the specification '{1}'".
                            format(self.value, tspec))


class Argument(object):
    """An argument specification."""

    def __init__(self, name, doc=None, tspec=None, vspec=None, **kwargs):
        if 'type' in kwargs:
            if not isinstance(kwargs['type'], list):
                kwargs['type'] = [kwargs['type']]
        if 'fixed' in kwargs:
            if kwargs['fixed'] is None:
                kwargs['none'] = True
        elif 'default' in kwargs:
            if kwargs['default'] is None:
                kwargs['none'] = True
        self.name = name
        self.doc = doc
        self.tspec = tspec or TypeSpec(**kwargs)
        self.vspec = vspec or ValueSpec(**kwargs)
        self.vspec &= self.tspec

    def __call__(self, func):
        signature = Signature.of(func)
        signature.arguments[self.name] = self + signature.arguments.get(self.name)
        return func

    def __str__(self):
        tdesc = str(self.tspec)
        vdesc = str(self.vspec)
        if len(tdesc) > 0:
            return tdesc + ", " + vdesc
        else:
            return vdesc

    def __add__(self, other):
        if other is None:
            return self
        if self.name != other.name:
            raise ArgumentError("Argument names do not match.")
        name = self.name
        doc = self.doc or other.doc
        tspec = self.tspec & other.tspec
        vspec = (self.vspec & other.tspec) + (other.vspec & self.tspec)
        return Argument(name, doc, tspec, vspec)

    def apply(self, args, name=None):
        """Applies this specification to a given argument."""
        name = name or self.name
        vspec = (name in args) and ValueSpec(fixed=args[name]) or ValueSpec()
        vspec &= self.tspec
        vspec += self.vspec
        if vspec.mode == ArgumentMode.REQUIRED:
            raise ArgumentError("Required argument '{0}' not provided.".format(name))
        args[name] = vspec.value

    mode = property(lambda self: self.vspec.mode)


def _original(callable_):
    while hasattr(callable_, 'func_dict') and MAGIC_ORG in callable_.func_dict:
        callable_ = callable_.func_dict[MAGIC_ORG]
    return callable_


class Signature(object):
    """Function signature specification.
    """

    @staticmethod
    def infer(callable_):
        """Infer a Signature for a given callable.
        """
        try:
            return Signature(*inspect.getargspec(callable_))
        except TypeError:
            return Signature(['self'])

    @staticmethod
    def of(callable_):                                         # pylint: disable-msg=C0103
        """Cache and return a Signature for a given callable.
        """
        if not hasattr(callable_, 'func_dict'):
            return Signature.infer(callable_)
        if MAGIC_SIG not in callable_.func_dict:
            callable_.func_dict[MAGIC_SIG] = Signature.infer(callable_)
        return callable_.func_dict[MAGIC_SIG]

    def __init__(self, names, positional=None, keyword=None, defaults=None):
        # TODO: flatten names
        self.positional = tuple(names)
        self.arguments = dict()
        self.extra_positional = positional
        self.extra_keyword = keyword
        if defaults is None:
            defaults = []
        required = len(self.positional) - len(defaults)
        for idx in range(required):
            name = names[idx]
            self.arguments[name] = Argument(name)
        for idx in range(len(defaults)):
            name = names[required+idx]
            self.arguments[name] = Argument(name, default=defaults[idx])

    def __str__(self):
        result = '{'
        for name, spec in self.arguments.iteritems():
            result += name
            result += ': '
            result += str(spec)
            result += '; '
        return result[:-2]+'}'

    def __iadd__(self, other):
        for name in self.arguments:
            self.arguments[name] += other.arguments.get(name)
        for name in other.arguments:
            if name not in self.arguments:
                self.arguments[name] = other.arguments[name]
        return self

    @property
    def Values(signature):                         # pylint: disable-msg=E0213,C0103,R0912
        """Return a class for argument values, specialized to match this Signature.
        """
        class ArgumentValues(object):
            """Holds argument values matching a given Specification.
            """
            def __init__(self, *args, **kwargs):               # pylint: disable-msg=C0103
                # parse arguments
                self.named = dict()
                self.named.update(kwargs)
                self.anonymous = []
                for index, value in enumerate(args):
                    if index < len(signature.positional):
                        name = signature.positional[index]
                        if name in self.named:
                            raise ArgumentError(
                                "{0} given both as a positional and keyword argument".
                                format(name))
                        self.named[name] = value
                    else:
                        self.anonymous.append(value)
                # apply specifications
                for name, spec in signature.arguments.iteritems():
                    spec.apply(self.named, name)

            def call(self, callable_, strict=True):
                """Call a given callable with these ArgumentValues.
                """
                signature = Signature.infer(callable_)
                args = []
                for name in signature.positional:
                    args.append(self.named[name])
                if signature.extra_positional:
                    args += self.anonymous
                kwargs = {}
                for name, value in self.named.iteritems():
                    if name in signature.positional:
                        continue
                    if name not in signature.arguments and not signature.extra_keyword:
                        if not strict:
                            continue
                        raise ArgumentError("Extra argument '{0}' given to {1}".
                                            format(name, callable_))
                    kwargs[name] = value
                return callable_(*tuple(args), **kwargs)       # pylint: disable-msg=W0142
        return ArgumentValues


class ObjectMeta(types.TypeType):
    """Metaclass for Object.
    """

    def __new__(mcs, name, bases, dict_):
        # replace constructor
        if '__init__' in dict_:
            init = dict_['__init__']
            def __init__(self, *args, **kwargs):               # pylint: disable-msg=C0103
                signature = Signature.of(__init__)
                values = signature.Values(self, *args, **kwargs)
                for parent in reversed(self.__class__.__mro__):
                    if '__init__' in parent.__dict__:
                        values.call(_original(parent.__init__), False)
            if hasattr(init, 'func_dict'):
                __init__.func_dict.update(init.func_dict)
            __init__.func_dict[MAGIC_SIG] = Signature.of(init)
            __init__.func_dict[MAGIC_ORG] = init
            __init__.__doc__ = init.__doc__                    # pylint: disable-msg=W0622
            dict_['__init__'] = __init__
        # call parent metaclass
        class_ = types.TypeType.__new__(mcs, name, bases, dict_)
        # collect constructor signature (requires __mro__ ordering)
        if '__init__' in dict_:
            for parent in class_.__mro__:
                if '__init__' in parent.__dict__:
                    parent_sig = Signature.of(_original(parent.__init__))
                    __init__.func_dict[MAGIC_SIG] += parent_sig
        return class_


class Object(object):
    """A replacement for object. Automatically manages signatures and call chain for
    constructors.
    """

    __metaclass__ = ObjectMeta


class DispatchOn(Object):
    """Decorator. Marks a single implementation of a dynamically-dispatched function.
    """

    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise ArgumentError("DispatchOn takes exactly one keyword argument")
        self.name = kwargs.keys[0]
        typ = kwargs[self.name]
        self.types = isinstance(typ, types.TupleType) and typ or (typ,)

    def __call__(self, function):
        combined = sys._getframe(1).f_locals.get(function.__name__)
        if combined is None:
            signature = Signature.infer(function)
            def _dispatch(*args, **kwargs):
                name = _dispatch.func_dict[MAGIC_DIS]
                values = signature.Values(*args, **kwargs)
                key = values.named[name]
                implementations = _dispatch.func_dict[MAGIC_MAP]
                class_ = isinstance(key, types.ClassType) and types.ClassType or key.__class__
                for parent in class_.__mro__:
                    if parent in implementations:
                        return values.call(implementations[parent])
                raise ArgumentError("Argument '{0}' for {1} is of unhandled type {2}".
                                    format(name, function.__name__, class_.__name__))
            combined = _dispatch
            combined.__name__ = function.__name__              # pylint: disable-msg=W0622
            combined.__doc__ = function.__doc__                # pylint: disable-msg=W0622
            combined.func_dict[MAGIC_SIG] = signature
            combined.func_dict[MAGIC_DIS] = self.name
            combined.func_dict[MAGIC_MAP] = dict()
        if combined.func_dict[MAGIC_DIS] != self.name:
            raise ArgumentError("Inconsistent names for dynamic dispatch arguments")
        for type_ in self.types:
            combined.func_dict[MAGIC_MAP][type_] = function
        return combined
