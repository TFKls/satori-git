#! module api
"""
A service that is used to bootstrap the client.
"""

from satori.objects import DispatchOn, Argument, ReturnValue, Throws
from satori.ars.wrapper import StaticWrapper, WrapperClass

class ApiServer(WrapperClass):
    server = StaticWrapper('Server')

    @server.method
    @ReturnValue(type=str)
    def getIDL():
        from satori.core.api import thrift_idl
        return thrift_idl

