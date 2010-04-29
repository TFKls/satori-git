# vim:ts=4:sts=4:sw=4:expandtab
"""Abstraction layer for various naming conventions.
"""

__all__ = (
    'Name',
    'ClassName', 'MethodName', 'ParameterName', 'FieldName', 'AccessorName',
    'NamedObject',
    'NamingStyle',
)


from satori.objects import Object, Argument, ArgumentError


class NameKind(Object):
    """Represents a kind of entity (class, function, etc.) that can be named.
    """

    @Argument('name', type=str)
    def __init__(self, name):
        self.name = name

    def __call__(self, string):
        return NameComponent(string, kind=self)

    def __str__(self):
        return 'NameKind:' + self.name

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

    def __str__(self):
        return "{0} ({1})".format(NamingStyle.DEFAULT.format(self), self.kind.name)


ClassName = NameKind(name="ClassName")
MethodName = NameKind(name="MethodName")
ParameterName = NameKind(name="ParameterName")
FieldName = NameKind(name="FieldName")
AccessorName = NameKind(name="AccessorName")


class Name(Object):
    """A hierarchical name.
    """

    ALLOWED = (
        (None, ClassName),
        (None, FieldName),
        (ClassName, ClassName),
        (ClassName, MethodName),
        (ClassName, FieldName),
        (FieldName, AccessorName),
        (None, MethodName),
        (None, ParameterName),
    )

    def __init__(self, *args):
        self.components = []
        self.hash = 0
        self.kind = None
        for arg in args:
            if not isinstance(arg, NameComponent):
                raise ArgumentError(
                    "Components of a Name must be instances of NameComponent:" + arg)
            if (self.kind, arg.kind) not in Name.ALLOWED:
                raise ArgumentError(
                    "A NameComponent of kind {0} cannot follow one of kind {1}".
                    format(arg.kind, self.kind))
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
        if isinstance(other, Name):
            plus = other.components
        else:
            plus = [other,]
        return Name(*(self.components + plus))

    def __str__(self):
        return 'Name:' + NamingStyle.DEFAULT.format(self)


class NamedObject(Object):
    """Mix-in base for Objects with a Name.
    """

    @Argument('name', type=Name)
    def __init__(self, name):
        self.name = name


class NamingStyle(Object):
    """Formatter corresponding to a specific naming convention.
    """

    def __init__(self, separator, formats, default_style):
        self.separator = separator
        self.formats = formats
        self.default_style = default_style

    def format(self, name):
        """Format a Name according to this NamingStyle.
        """
        if isinstance(name, NameComponent):
            return self.formats.get(name.kind, self.default_style)(name)
        if isinstance(name, Name):
            return self.separator.join([self.format(c) for c in name.components])
        raise TypeError(
            "The argument to NamingStyle.format() must be a Name or a NameComponent")

    def parse(self, string):
        """Tries to parse the string.
        """
        def looks_like(crumb, kind):
            return crumb == self.formats.get(kind, self.default_style)(kind(crumb))

        crumbs = string.split(self.separator)
        if not crumbs:
            return []
        res = []
        for i, kind in Name.ALLOWED:
            if i is None and looks_like(crumbs[0], kind):
                res.append(Name(kind(crumbs[0])))
        for crumb in crumbs[1:]:
            nres = []
            for name in res:
                for prev, next in Name.ALLOWED:
                    if prev is name.kind and looks_like(crumb, next):
                        nres.append(name + next(crumb))
            res = nres
        return res

    PASCAL = staticmethod(
        lambda c: ''.join([w.lower().capitalize() for w in c.words]))
    MIXED = staticmethod(
        lambda c: ''.join([c.words[0].lower()] +
                          [w.lower().capitalize() for w in c.words[1:]]))
    LOWER = staticmethod(
        lambda c: '_'.join([w.lower() for w in c.words]))
    UPPER = staticmethod(
        lambda c: '_'.join([w.upper() for w in c.words]))

NamingStyle.DEFAULT = NamingStyle('.', {ClassName: NamingStyle.PASCAL}, NamingStyle.MIXED)
NamingStyle.IDENTIFIER = NamingStyle('_', {ClassName: NamingStyle.PASCAL}, NamingStyle.MIXED)
NamingStyle.PYTHON = NamingStyle('__', {ClassName: NamingStyle.PASCAL}, NamingStyle.LOWER)

