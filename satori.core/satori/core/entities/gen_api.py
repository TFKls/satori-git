#! module api

from StringIO import StringIO

from satori.ars import wrapper
from satori.ars.thrift import ThriftWriter
from satori.core import cwrapper

from satori.core.api import *

wrapper.register_middleware(cwrapper.TransactionMiddleware())

wrapper.register_middleware(cwrapper.TokenVerifyMiddleware())
wrapper.global_throws(cwrapper.TokenInvalid)
wrapper.global_throws(cwrapper.TokenExpired)

wrapper.register_middleware(wrapper.TypeConversionMiddleware())

wrapper.register_middleware(cwrapper.CheckRightsMiddleware())

ars_interface = wrapper.generate_interface()

writer = ThriftWriter()
idl_io = StringIO()
writer.write_to(ars_interface, idl_io)
thrift_idl = idl_io.getvalue()

del writer
del idl_io

