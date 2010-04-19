# vim:ts=4:sts=4:sw=4:expandtab
"""Provider for the thrift protocol.
"""


from satori.objects import Object, Argument, DispatchOn, ArgumentError
from satori.ars.naming import NamedObject, NamingStyle
from satori.ars.model import AtomicType, Boolean, Int16, Int32, Int64, String, Void
from satori.ars.model import Field, ListType, MapType, SetType, Structure, TypeAlias
from satori.ars.model import Element, Parameter, Procedure, Contract
from satori.ars.common import TopologicalWriter


class ThriftBase(Object):

    @Argument('style', type=NamingStyle, default=NamingStyle.IDENTIFIER)
    def __init__(self, style):
        self.style = style


class ThriftWriter(TopologicalWriter, ThriftBase):
    """An ARS Writer spitting out thrift IDL.
    """

    ATOMIC_NAMES = {
        Boolean: 'bool',
        Int16:   'i16',
        Int32:   'i32',
        Int64:   'i64',
        String:  'string',
        Void:    'void',
    }

    @DispatchOn(item=object)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=NamedObject)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write(self.style.format(item.name))

    @DispatchOn(item=AtomicType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write(ThriftWriter.ATOMIC_NAMES[item])

    @DispatchOn(item=ListType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('list<')
        self._reference(item.element_type, target)
        target.write('>')

    @DispatchOn(item=MapType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('map<')
        self._reference(item.key_type, target)
        target.write(',')
        self._reference(item.value_type, target)
        target.write('>')

    @DispatchOn(item=SetType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('set<')
        self._reference(item.element_type, target)
        target.write('>')

    @DispatchOn(item=Element)
    def _write(self, item, target): # pylint: disable-msg=E0102
        raise ArgumentError("Unknown Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=(AtomicType,ListType,MapType,SetType,Field,Parameter,Procedure))
    def _write(self, item, target): # pylint: disable-msg=E0102
        pass

    @DispatchOn(item=TypeAlias)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('typedef ')
        self._reference(item.target_type, target)
        target.write(' ')
        self._reference(item, target)
        target.write('\n')

    @DispatchOn(item=Structure)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('struct ')
        self._reference(item, target)
        sep = ' {\n\t'
        ind = 1
        for field in item.fields:
            target.write('{0}{1}:'.format(sep, ind))
            if field.optional:
                target.write('optional ')
            self._reference(field.type, target)
            target.write(' ')
            self._reference(field, target)
            sep = '\n\t'
            ind += 1
        target.write('\n}\n')

    @DispatchOn(item=Contract)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('service ')
        self._reference(item, target)
        sep = ' {\n\t'
        for procedure in item.procedures:
            target.write(sep)
            self._reference(procedure.return_type, target)
            target.write(' ')
            self._reference(procedure, target)
            target.write('(')
            sep2 = ''
            ind = 1
            for parameter in procedure.parameters:
                target.write('{0}{1}:'.format(sep2, ind))
                if parameter.optional:
                    target.write('optional ')
                self._reference(parameter.type, target)
                target.write(' ')
                self._reference(parameter, target)
                if parameter.default is not None:
                    target.write(' = {0}'.format(parameter.default))
                sep2 = ', '
                ind += 1
            target.write(')')
            if procedure.error_type is not Void:
                target.write(' throws (0:')
                self._reference(procedure.error_type, target)
                target.write(' error)')
            sep = '\n\t'
        target.write('\n}\n')
