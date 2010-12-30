# vim:ts=4:sts=4:sw=4:expandtab

@ExportClass
class Server(object):
    """
    """
    @ExportMethod(unicode, [], PCPermit())
    def getIDL():
        from satori.core.api import thrift_idl
        return thrift_idl
