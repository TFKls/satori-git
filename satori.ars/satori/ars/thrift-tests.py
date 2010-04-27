from multiprocessing import Process 
from unittest import TestCase
from time import sleep

from ..thrift.Thrift import TType, TMessageType, TApplicationException
from ..thrift.transport.TSocket import TSocket, TServerSocket
from ..thrift.protocol.TBinaryProtocol import TBinaryProtocol

from satori.ars.naming import Name, ClassName, MethodName, ParameterName
from satori.ars.model import Contract, Procedure, Parameter, String
from satori.ars.thrift import ThriftWriter, ThriftServer


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
                void doNothing() throws (1:string error)
            }
        """)


class Server(TestCase):
    
    @staticmethod
    def echo(string):
        return string

    def setUp(self):
        procedure = Procedure(name=Name(MethodName('echo')), return_type=String,
            implementation=Server.echo)
        procedure.addParameter(name=Name(ParameterName('string')), type=String)
        contract = Contract(name=Name(ClassName('test')))
        contract.addProcedure(procedure)
        server = ThriftServer(transport=TServerSocket())
        server.contracts.add(contract)
        self.server_process = Process(target=server.run)
        self.server_process.start()
        sleep(1)
        self.transport = TSocket()
        self.transport.open()
        self.protocol = TBinaryProtocol(self.transport) 

    def testEcho(self):
        message = 'Hello, World!'
        self.protocol.writeMessageBegin('echo', TMessageType.CALL, 1)
        self.protocol.writeStructBegin('echo_arguments')
        self.protocol.writeFieldBegin('string', TType.STRING, 1)
        self.protocol.writeString(message)
        self.protocol.writeFieldEnd()
        self.protocol.writeFieldStop()
        self.protocol.writeStructEnd()
        self.protocol.writeMessageEnd()
        self.protocol.trans.flush()
        name, type, seqid = self.protocol.readMessageBegin()
        self.assertEqual(name, 'echo')
        self.assertEqual(type, TMessageType.REPLY)
        self.assertEqual(seqid, 1)
        self.protocol.readStructBegin()
        name, type, index = self.protocol.readFieldBegin()
        self.assertEqual(type, TType.STRING)
        self.assertEqual(index, 0)
        self.assertEqual(message, self.protocol.readString())
        self.protocol.readFieldEnd()
        name, type, index = self.protocol.readFieldBegin()
        self.assertEqual(type, TType.STOP)
        self.protocol.readStructEnd()
        self.protocol.readMessageEnd()
    
    def tearDown(self):
        self.transport.close()
        self.server_process.terminate()
