#! module models

from satori.core.export import ExportClass, ExportMethod, PCPermit

@ExportClass
class Server(object):
    
    @ExportMethod(unicode, [], PCPermit())
    def getIDL():
        from satori.core.api import thrift_idl
        return thrift_idl

