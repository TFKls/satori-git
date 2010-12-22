# vim:ts=4:sts=4:sw=4:expandtab

import sys

from django.core.management.base import NoArgsCommand
    
from satori.ars.thrift import ThriftWriter
from satori.core.api import ars_interface

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        writer = ThriftWriter()
        writer.write_to(ars_interface, sys.stdout)

