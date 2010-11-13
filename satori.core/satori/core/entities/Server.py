

@ExportClass
class Server(object):
    
    @ExportMethod(unicode, [], PCPermit())
    def getIDL():
        from satori.core.api import thrift_idl
        return thrift_idl

