from unittest import TestCase

from satori.ars.naming import Name, ClassName, MethodName
from satori.ars.model import Contract, Procedure
from satori.ars.thrift import ThriftWriter


class Writer(TestCase):

    def setUp(self):
        self.text = None
        self.pTrivial = Procedure(name=Name(MethodName('do_nothing')))

    def clear(self):
        self.text = ''

    def write(self, data):
        self.text += data

    def verify(self, valid):
        self.assertEqual(' '.join(self.text.split()).strip(), ' '.join(valid.split()).strip())

    def testTrivial(self):
        contract = Contract(name=Name(ClassName('test')))
        contract.addProcedure(self.pTrivial)
        self.clear()
        writer = ThriftWriter()
        writer.contracts.add(contract)
        writer.writeTo(self)
        self.verify("""
            service Test {
                void doNothing() throws (0:string error)
            }
        """)
