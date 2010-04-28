# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""


def export_thrift():
    """Entry Point. Writes the Thrift contract of the server to standard output.
    """
    from sys import stdout
    import satori.core.models
    from satori.ars import django2ars
    from satori.ars.thrift import ThriftWriter
    writer = ThriftWriter()
    writer.contracts = django2ars.contracts
    writer.writeTo(stdout)
