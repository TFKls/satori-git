# vim:ts=4:sts=4:sw=4:expandtab
"""Useful additions to the standard Python class hierarchy.
"""


__all__ = (
    'Object', 'Argument', 'ArgumentMode', 'ArgumentError',
)

import six
from inspect import getargspec
from sys import _getframe

if six.PY2:
    from types import ClassType, DictType, NoneType, TupleType
else:
    ClassType = type
    DictType = dict
    NoneType = type(None)
    TupleType = tuple


class Namespace(dict):
    """A dictionary whose elements can be accessed as attributes.
    """

    def __init__(self, *args, **kwargs):
        super(Namespace, self).__init__(*args, **kwargs)

    def __hasattr__(self, key):
        return key in self

    def __getattribute__(self, key):
        try:
            return self[key]
        except KeyError:
            return super(Namespace, self).__getattribute__(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

class NoneObj(object):
    def __init__(self, obj):
        self.__obj = obj

    def __getattribute__(self, key):
        try:
            return super(NoneObj, self).__getattribute__(key)
        except:
            try:
                return getattr(self.__obj, key)
            except:
                return None

MAGIC_ORG = 'objects/original'
MAGIC_SIG = 'objects/signature'
MAGIC_DIS = 'objects.DispatchOn/argument name'
MAGIC_MAP = 'objects.DispatchOn/type map'

class ArgumentError(Exception):
    """Exception. A problem with an argument's specification or value.
    """
    pass


class ArgumentConstraint(object):
    """Abstract. A constraint for function argument.
    """

    def invalid(self, value):
        """Checks whether a given value satisfies this constraint.
        Returns the error message or None if the constraint is satisfied.
        """
        raise NotImplementedError()

    def __le__(self, other):
        """Checks whether this constraint is stronger than (or equal to) another.

        The set of all ArgumentConstraints with this relation should form a partial order.
        """
        if isinstance(other, NoConstraint):
            return True
        if isinstance(other, ConstraintConjunction):
            return all(self <= m for m in other.members)
        if isinstance(other, ConstraintDisjunction):
            return any(self <= m for m in other.members)
        return False

    def __eq__(self, other):
        return (self <= other) and (other <= self)

    def __and__(self, other):
        if isinstance(other, (ConstraintConjunction, ConstraintDisjunction)):
            return other & self
        return ConstraintConjunction.of((self, other))

    def __or__(self, other):
        if isinstance(other, (ConstraintConjunction, ConstraintDisjunction)):
            return other | self
        return ConstraintDisjunction.of((self, other))

    @staticmethod
    def parse(spec):
        if spec is None:
            return TypeConstraint(NoneType)
        if isinstance(spec, six.class_types):
            return TypeConstraint(spec)
        if isinstance(spec, TupleType):
            return ConstraintDisjunction.of([
                ArgumentConstraint.parse(m) for m in spec
            ])
        if isinstance(spec, DictType):
            handlers = {
                'type': ArgumentConstraint.parse
            }
            return ConstraintConjunction.of([
                handlers.get(k, lambda v: None)(v) for k, v in six.iteritems(spec)
            ])
        raise ArgumentError(
            "Unrecognized argument constraint specification '{0}'"
            .format(spec)
        )


class NoConstraint(ArgumentConstraint):
    """An ArgumentConstraint which is always satisfied.
    """

    def invalid(self, value):
        return None

    def __and__(self, other):
        return other

    def __or__(self, other):
        return self

    def __str__(self):
        return "anything"


class ConstraintConjunction(ArgumentConstraint):
    """A conjunction of multiple ArgumentConstraints.
    """

    def __init__(self, members):
        self.members = tuple(members)

    @staticmethod
    def of(candidates):
        members = []
        for i, c in enumerate(candidates):
            if c is None:
                continue
            if any(d <= c for d in candidates[i+1:]):
                continue
            if any(m <= c for m in members):
                continue
            members.append(c)
        if len(members) == 0:
            return NoConstraint()
        elif len(members) == 1:
            return members[0]
        else:
            ConstraintConjunction(members)

    def invalid(self, value):
        for member in self.members:
            result = member.invalid(value)
            if result is not None:
                return result
        return None

    def __le__(self, other):
        return any(m <= other for m in self.members)

    def __and__(self, other):
        plus = isinstance(other, ConstraintConjunction) and other.members or [other]
        return ConstraintConjunction.of(self.members + plus)

    def __or__(self, other):
        return ConstraintConjunction.of([m | other for m in self.members])

    def __str__(self):
        return " and ".join("({0})".format(m) for m in self.members)


class ConstraintDisjunction(ArgumentConstraint):
    """A disjunction of multiple ArgumentConstraints.
    """

    def __init__(self, members):
        self.members = tuple(members)

    @staticmethod
    def of(candidates):
        members = []
        for i, c in enumerate(candidates):
            if c is None:
                continue
            if any(c <= d for d in candidates[i+1:]):
                continue
            if any(c <= m for m in members):
                continue
            members.append(c)
        if len(members) == 0:
            raise ArgumentError("ConstraintDisjunction must have at least one member!")
        elif len(members) == 1:
            return members[0]
        else:
            return ConstraintDisjunction(members)

    def invalid(self, value):
        results = []
        for member in self.members:
            result = member.invalid(value)
            if result is None:
                return None
            results.append(result)
        return '; '.join(results)

    def __le__(self, other):
        return all(m <= other for m in self.members)

    def __and__(self, other):
        return ConstraintDisjunction.of([m & other for m in self.members])

    def __or__(self, other):
        plus = isinstance(other, ConstraintDisjunction) and other.members or [other]
        return ConstraintDisjunction.of(self.members + plus)

    def __str__(self):
        return " or ".join("({0})".format(m) for m in self.members)


class TypeConstraint(ArgumentConstraint):
    """Constraint. Requires the value to be an instance of a specific type.
    """

    def __init__(self, type_):
        self.type = type_

    def invalid(self, value):
        if isinstance(value, self.type):
            return None
        return "{0} is not an instance of {1}".format(value, self.type)

    def __le__(self, other):
        if isinstance(other, TypeConstraint):
            return issubclass(self.type, other.type)
        return super(TypeConstraint, self).__le__(other)

    def __str__(self):
        return "instance of {0}".format(self.type)


class ArgumentMode(object):
    """Enumeration. Modes for function arguments.
    """

    REQUIRED = 0
    OPTIONAL = 1
    PROVIDED = 2


class Argument(object):
    """An argument specification.
    """

    def _enforce(self, constraint):
        if self.mode != ArgumentMode.REQUIRED:
            error = constraint.invalid(self.value)
            if error is not None:
                if self.mode == ArgumentMode.PROVIDED:
                    raise ArgumentError("Invalid provided value: "+error)
                self.mode = ArgumentMode.REQUIRED
        self.constraint &= constraint

    def __init__(self, name, doc=None, **kwargs):
        self.name = name
        self.doc = doc
        self.constraint = NoConstraint()
        self.mode = kwargs.pop('mode', ArgumentMode.REQUIRED)
        self.value = kwargs.pop('value', None)
        if 'default' in kwargs:
            self.value = kwargs.pop('default')
            self.mode = ArgumentMode.OPTIONAL
        if 'fixed' in kwargs:
            self.value = kwargs.pop('fixed')
            self.mode = ArgumentMode.PROVIDED
        self._enforce(kwargs.pop('constraint', None) or ArgumentConstraint.parse(kwargs))

    def __call__(self, func):
        signature = Signature.of(func)
        signature.arguments[self.name] = self + signature.arguments.get(self.name)
        return func

    def __str__(self):
        if self.mode == ArgumentMode.REQUIRED:
            return "required, {0}".format(self.constraint)
        if self.mode == ArgumentMode.OPTIONAL:
            return "optional (default = {0}), {1}".format(self.value, self.constraint)
        if self.mode == ArgumentMode.PROVIDED:
            return "fixed (value = {0})".format(self.value)
        raise Exception('this should NOT happen!')

    def __add__(self, other):
        if other is None:
            return self
        if self.name != other.name:
            raise ArgumentError("Argument names do not match.")
        name = self.name
        doc = self.doc or other.doc
        cons = self.constraint & other.constraint
        left = Argument(name, doc, constraint=cons, mode=self.mode, value=self.value)
        right = Argument(name, doc, constraint=cons, mode=other.mode, value=other.value)
        if left.mode == ArgumentMode.REQUIRED:
            return right
        if right.mode == ArgumentMode.REQUIRED:
            return left
        if left.mode == ArgumentMode.PROVIDED and right.mode == ArgumentMode.PROVIDED:
            if left.value != right.value:
                raise ArgumentError(
                    "Conflicting provided values: {0} and {1}"
                    .format(left.value, right.value)
                )
        if right.mode == ArgumentMode.PROVIDED:
            return right
        else:
            return left

    def apply(self, args, name=None):
        """Applies this specification to a given argument."""
        name = name or self.name
        provided = (name in args) and Argument(name, fixed=args[name]) or Argument(name)
        provided += self
        if provided.mode == ArgumentMode.REQUIRED:
            raise ArgumentError("Required argument '{0}' not provided.".format(name))
        args[name] = provided.value

class ReturnValue(object):
    """A return value specification.
    """

    def __init__(self, **kwargs):
        self.constraint = (kwargs.pop('constraint', None) or ArgumentConstraint.parse(kwargs) or NoConstraint())

    def __call__(self, func):
        signature = Signature.of(func)
        signature.return_value = self + signature.return_value
        return func

    def __str__(self):
        return "{0}".format(self.constraint)

    def __add__(self, other):
        if other is None:
            return self
        cons = self.constraint & other.constraint
        return ReturnValue(constraint=cons)

    def apply(self, value):
        """Applies this specification to a return value."""
        error = self.constraint.invalid(value)
        if error is not None:
            raise TypeError("Bad return value type: " + error)


class Throws(object):
    """A thrown exception specification.
    """

    def __init__(self, exception):
        self.exception = exception

    def __call__(self, func):
        signature = Signature.of(func)
        signature.exceptions.append(self.exception)
        return func


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
            return Signature(*getargspec(callable_))
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
        self.return_value = ReturnValue()
        self.exceptions = []
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
        return result[:-2] + '}' + '->' + str(self.return_value)

    def __iadd__(self, other):
        for name in self.arguments:
            self.arguments[name] += other.arguments.get(name)
        for name in other.arguments:
            if name not in self.arguments:
                self.arguments[name] = other.arguments[name]
        return self

    def remove_argument(self, name):
        if name in self.arguments:
            positional = list(self.positional)
            positional.remove(name)
            del self.arguemnts[name]

    def set(self, callable_):                                         # pylint: disable-msg=C0103
        """Set this Signature for a given callable.
        """
        if hasattr(callable_, 'func_dict'):
            callable_.func_dict[MAGIC_SIG] = self

    @property
    def Values(signature):                         # pylint: disable-msg=E0213,C0103,R0912
        """Return a class for argument values, specialized to match this Signature.
        """
        class ArgumentValues(object):
            """Holds argument values matching a given Signature.
            """
            def __init__(*args, **kwargs):               # pylint: disable-msg=C0103
                # parse arguments
                self = args[0]
                self.named = dict()
                self.named.update(kwargs)
                self.anonymous = []
                for index, value in enumerate(args[1:]):
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
                for name, spec in six.iteritems(signature.arguments):
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
                for name, value in six.iteritems(self.named):
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


class ObjectMeta(type):
    """Metaclass for Object.
    """

    def __new__(mcs, name, bases, dict_):
        # replace constructor
        init = dict_.get('__init__', lambda self: None)
        def __init__(*args, **kwargs):               # pylint: disable-msg=C0103
            self = args[0]
            signature = Signature.of(__init__)
            values = signature.Values(*args, **kwargs)
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
        class_ = type.__new__(mcs, name, bases, dict_)
        # collect constructor signature (requires __mro__ ordering)
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
        for key in kwargs.keys():
            self.name = key
        typ = kwargs[self.name]
        self.types = isinstance(typ, TupleType) and typ or (typ,)

    def __call__(self, function):
        combined = _getframe(1).f_locals.get(function.__name__)
        if combined is None:
            signature = Signature.infer(function)
            def _dispatch(*args, **kwargs):
                name = _dispatch.func_dict[MAGIC_DIS]
                values = signature.Values(*args, **kwargs)
                key = values.named[name]
                implementations = _dispatch.func_dict[MAGIC_MAP]
                class_ = isinstance(key, ClassType) and ClassType or key.__class__
                for parent in class_.__mro__:
                    if parent in implementations:
                        return values.call(implementations[parent])
                raise ArgumentError("Argument '{0}' for {1} is of unhandled type {2}".
                                    format(name, function.__name__, class_.__name__))
            combined = _dispatch
            combined.__name__ = function.__name__              # pylint: disable-msg=W0622
            combined.__doc__ = function.__doc__                # pylint: disable-msg=W0622
            if not hasattr(combined, 'func_dict'):
                combined.func_dict = { }
            combined.func_dict[MAGIC_SIG] = signature
            combined.func_dict[MAGIC_DIS] = self.name
            combined.func_dict[MAGIC_MAP] = dict()
        if combined.func_dict[MAGIC_DIS] != self.name:
            raise ArgumentError("Inconsistent names for dynamic dispatch arguments")
        oldmap = getattr(function, 'func_dict', {}).get(MAGIC_MAP, {})
        if oldmap:
            combined.func_dict[MAGIC_MAP].update(oldmap)
            function = function.func_dict[MAGIC_ORG]
        for type_ in self.types:
            combined.func_dict[MAGIC_MAP][type_] = function
        combined.func_dict[MAGIC_ORG] = function
        return combined
