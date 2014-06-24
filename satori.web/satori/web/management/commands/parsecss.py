from six import print_
# vim:ts=4:sts=4:sw=4:expandtab
import cssutils
import os
from django.conf import settings
from django.core.management.base import NoArgsCommand
from optparse import make_option

def add_main_selector(rules, main_selector):
    for rule in rules:
        if rule.type == rule.STYLE_RULE:
            for selector in rule.selectorList:
                selector.selectorText = '{0} {1}'.format(main_selector,
                        selector.selectorText)
        elif rule.type == rule.MEDIA_RULE:
            add_main_selector(rule.cssRules, main_selector)

class Command(NoArgsCommand):
    help='Regenerate sphinx css files to make them compatible with Satori.'
    option_list = NoArgsCommand.option_list + (
        make_option('-f', '--files', action='store', dest='files',
            help='CSS files that should be regenerated'),
        make_option('-d', '--destination', action='store', dest='dest', 
            help='Output directory'),
    )

    def handle_noargs(self, **options):
        if options['files'] == None or options['dest'] == None:
            print_('Please provide all necessary arguments')
            return

        files = options['files'].split(',')
        for css_file in files:
            input_file = open(css_file,'r')
            sheet = cssutils.parseString(input_file.read())
            input_file.close()

            # TODO(kalq): Make the name of the main selector a constant
            add_main_selector(sheet, '.mainsphinx')

            output_file = open(os.path.join(options['dest'], os.path.basename(css_file)), 'w')
            output_file.write(sheet.cssText)
            output_file.close()
