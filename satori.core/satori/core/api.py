# vim:ts=4:sts=4:sw=4:expandtab

from StringIO import StringIO

from satori.ars.thrift import ThriftWriter
from satori.core.export import generate_interface

import satori.core.models

ars_interface = generate_interface()

writer = ThriftWriter()
idl_io = StringIO()
writer.write_to(ars_interface, idl_io)
thrift_idl = idl_io.getvalue()

del writer
del idl_io

