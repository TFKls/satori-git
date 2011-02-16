# vim:ts=4:sts=4:sw=4:expandtab

import sys

from optparse import make_option

from django.core.management.base import NoArgsCommand
    
from satori.ars.thrift import ThriftWriter
from satori.core.api import ars_interface

class Command(NoArgsCommand):
    help = ("Creates Thrift IDL")

    option_list = NoArgsCommand.option_list + (
        make_option('--output', action='store', dest='output',
            default='-', help='Output file.'),
    )

    requires_model_validation = True

    def handle_noargs(self, **options):
        writer = ThriftWriter()
        outfile = options.get('output', '-')
        if outfile != '-':
            out = open(outfile, 'w')
        else:
            out = sys.stdout
        writer.write_to(ars_interface, out)
        if outfile != '-':
            out.close()
