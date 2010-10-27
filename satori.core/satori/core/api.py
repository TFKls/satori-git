from StringIO import StringIO

from satori.ars.thrift import ThriftWriter
from satori.core.export import generate_interface

import satori.core.models

import satori.core.export
import satori.core.sec
satori.core.export.Token = satori.core.sec.Token
satori.core.models.Token = satori.core.sec.Token
satori.core.export.Privilege = satori.core.models.Privilege

ars_interface = generate_interface()

writer = ThriftWriter()
idl_io = StringIO()
writer.write_to(ars_interface, idl_io)
thrift_idl = idl_io.getvalue()

del writer
del idl_io

