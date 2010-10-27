# vim:ts=4:sts=4:sw=4:expandtab

import _ast
import ast
import imp
import os
import re
import sys
import traceback
from StringIO import StringIO
from _topsort import topsort, CycleError

names = ['models']

class SatoriLoader(object):
    def load_file(self, filename, fullname):
        modulename = fullname.rsplit('.', 1)[1]

        with open(filename, 'r') as f:
            in_module = False
            modulecode = StringIO()
            uses = set()
            for line in f:
                if line.startswith(r'#! module '):
                    in_module = line.startswith(r'#! module ' + modulename)

                if in_module:
                    m = re.match(r'^from +{0} +import (.*)$'.format(fullname), line)

                    if m:
                        uses.update([x.strip() for x in m.group(1).split(',')])
                        modulecode.write('\n')
                    else:
                        modulecode.write(line)
                else:
                    modulecode.write('\n')

            code = compile(modulecode.getvalue(), filename, 'exec')

            provides = set()
            moduleast = ast.parse(modulecode.getvalue())
            for node in moduleast.body:
                if isinstance(node, _ast.Assign):
                    provides.update([x.id for x in node.targets])
                if isinstance(node, _ast.ClassDef):
                    provides.add(node.name)

        return (code, uses, provides)

    def load_module(self, fullname):
        module = sys.modules.setdefault(fullname, imp.new_module(fullname))
        module.__file__ = '<{0}>'.format(fullname)

        modules = []
        for filename in os.listdir(__path__[0]):
            if re.match(r'^[a-zA-Z][_a-zA-Z]*\.py$', filename):
                modules.append(self.load_file(os.path.join(__path__[0], filename), fullname))
        
        pairs = []

        for (code, uses, provides) in modules:
            for (code2, uses2, provides2) in modules:
                if code != code2:
                    if provides & provides2:
                        print 'Two modules provide {0}'.format(str(provides & provides2))
                        raise ImportError('Two modules provide {0}'.format(str(provides & provides2)))
        
        for (code, uses, provides) in modules:
            for use in uses:
                if use == '*':
                    for (code2, uses2, provides2) in modules:
                        if code != code2:
                            pairs.append((code2, code))
                    continue

                second = None

                for (code2, uses2, provides2) in modules:
                    if use in provides2:
                        second = code2

                if second is None:
                    print 'No module provides {0}'.format(use)
                    raise ImportError('No module provides {0}'.format(use))

                pairs.append((second, code))

            pairs.append((None, code))

        try:
            for code in topsort(pairs):
                if code is not None:
                    exec code in module.__dict__
        except CycleError:
            print 'There is a cycle in module dependencies'
            raise ImportError('There is a cycle in module dependencies')

        return module


class SatoriFinder(object):
    def find_module(self, fullname, path=None):
        splitname = fullname.rsplit('.', 1)

        if (len(splitname) == 2) and (splitname[0] == 'satori.core') and (splitname[1] in names):
            return SatoriLoader()
        else:
            return None

sys.meta_path.append(SatoriFinder())

