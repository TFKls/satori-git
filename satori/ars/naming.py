"""
Abstracts away the differences between various naming conventions.
"""

__all__ = (
    'Name',
    'ClassName', 'MethodName', 'FieldName', 'AccessorName',
    'NamedObject',
    'NamingStyle',
)


from satori.ph.objects import Object, Argument
from satori.ph.exceptions import ArgumentError


class NameKind(Object):
    """Represents a kind of entity (class, function, etc.) that can be named.
    """

    @Argument('name', type=str)
    def __init__(self, name):
        self.name = name

    def __call__(self, string):
        return Name(NameComponent(string=string, kind=self))


class NameComponent(Object):
    """A single component of a hierarchical name.
    """

    @Argument('string', type=str)
    @Argument('kind', type=NameKind)
    def __init__(self, string, kind):
        self.kind = kind
        self.hash = hash(self.kind)
        self.words = []
        for word in string.split():
            for part in word.split('_'):
                if len(part) == 0:
                    continue
                if part.isupper():
                    self._append(part)
                else:
                    left = 0
                    while left < len(part):
                        right = left + 1
                        while part[right:right+1].islower():
                            right += 1
                        self._append(part[left:right])
                        left = right
        if len(self.words) == 0:
            raise ArgumentError("A NameComponent must consist of at least one word")

    def _append(self, word):
        self.hash ^= hash(word)
        self.words.append(word)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if not isinstance(other, NameComponent):
            return False
        if self.hash != other.hash:
            return False
        return (self.words == other.words)


ClassName = NameKind(name="ClassName")
MethodName = NameKind(name="MethodName")
ArgumentName = NameKind(name="ArgumentName")
FieldName = NameKind(name="FieldName")
AccessorName = NameKind(name="AccessorName")


class Name(Object):
    """A hierarchical name.
    """

    ALLOWED = (
        (None, ClassName),
        (None, MethodName),
        (None, FieldName),
        (ClassName, ClassName),
        (ClassName, MethodName),
        (ClassName, FieldName),
        (MethodName, ArgumentName),
        (FieldName, FieldName),
        (FieldName, AccessorName),
    )

    def __init__(self, *args, **kwargs):
        super(Name, self).__init__()
        self.components = []
        self.hash = 0
        self.kind = None
        for arg in args:
            if not isinstance(arg, NameComponent):
                raise ArgumentError("Components of a Name must be instances of NameComponent")
            if (self.kind, arg.kind) not in Name.ALLOWED:
                raise ArgumentError("A NameComponent of kind {0} cannot follow one of kind {1}".format(arg.kind, self.kind))
            self.components.append(arg)
            self.hash ^= hash(arg)
            self.kind = arg.kind
        if self.kind is None:
            raise ArgumentError("A Name must have at least one component")

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if not isinstance(other, Name):
            return False
        if self.hash != other.hash:
            return False
        return (self.components == other.components)

    def __add__(self, other):
        return Name(*(self.components + other.components))


class NamedObject(Object):
    """Mix-in base for Objects with a Name.
    """

    @Argument('name', type=Name)
    def __init__(self, args):
        self.name = args.name


class NamingStyle(Object):
    """Formatter corresponding to a specific naming convention.
    """

    def __init__(self):
        self.formats = dict()

    def format(self, name):
        """Format a Name according to this NamingStyle.
        """
        if isinstance(name, NameComponent):
            return self.formats.get(name.kind, NamingStyle.CAMEL)(name)
        if isinstance(name, Name):
            return '.'.join([self.format(c) for c in name.components])
        raise TypeError("The argument to NamingStyle.format() must be a Name or a NameComponent")

    CAMEL = staticmethod(lambda component: ''.join([w.lower().capitalize() for w in component.words]))
    PASCAL = staticmethod(lambda component: ''.join([component.words[0].lower()] + [w.lower().capitalize() for w in component.words[1:]]))
    LOWER = staticmethod(lambda component: '_'.join([w.lower() for w in component.words]))
    UPPER = staticmethod(lambda component: '_'.join([w.upper() for w in component.words]))
