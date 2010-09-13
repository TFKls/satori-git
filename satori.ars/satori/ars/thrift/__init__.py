# vim:ts=4:sts=4:sw=4:expandtab
"""Provider for the thrift protocol.
"""

from reader import ThriftReader
from writer import ThriftWriter
from client import ThriftClient, bootstrap_thrift_client
from server import ThriftServer

