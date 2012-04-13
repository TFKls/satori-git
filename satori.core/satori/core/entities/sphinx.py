
SphinxException = DefineException('SphinxException', 'Sphinx error: {error}', [('error', unicode, False)])

import re
import sys, os, shutil
import subprocess
import logging
from copy import deepcopy
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from tempfile import mkdtemp
from sphinx.application import Sphinx
from sphinx.errors import PycodeError, SphinxError


# HACK

def do_hack():
    import sphinx.writers.latex

    class NewLatexTranslator(sphinx.writers.latex.LaTeXTranslator):
        def visit_reference(self, node):
            self.context.append('')

    sphinx.writers.latex.LaTeXTranslator = NewLatexTranslator

do_hack()

# HACK END


CORE_PATH = os.path.abspath(os.path.split(__file__)[0])

config_overrides = {
    'extensions' : ['sphinx.ext.pngmath','sphinx.ext.graphviz', 'satori.core.models'],
    'templates_path' : [os.path.join(CORE_PATH, 'sphinx_templates')],
    'source_suffix' : '.rst',
    'master_doc' : 'index',
    'project' : u'',
    'copyright': u'',
    'version' : '1',
    'release' : '1',
    'exclude_patterns' : ['_build'],
    'pygments_style' : 'sphinx',
    'pngmath_use_preview' : True,
    'pngmath_latex_preamble' : r'\usepackage{amsmath} \usepackage{polski}',

#    'html_theme' : 'default',
#    'html_theme_path' : [os.path.join(CORE_PATH, 'sphinx_templates')],
#    'html_static_path' : ['_static'],
    'htmlhelp_basename' : '',

    'latex_documents': [('index', 'index.tex', '', '', 'article')],
    'latex_elements': {
            'papersize': 'a4paper',
            'pointsize': '12pt',
            'fontpkg': '',
            'fncychap': '',
            }
}


class TexNode(nodes.Element):
    def __init__(self, *args, **kwargs):
        super(TexNode, self).__init__()
        self.attributes['value'] = kwargs['value']


def visit_tex_node_tex(self, node):
    self.body.append(node.attributes['value'])


def visit_tex_node_other(self, node):
    pass


def depart_tex_node(self, node):
    pass


class PdfInfoDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
            'leftlogo': directives.unchanged,
            'rightlogo': directives.unchanged,
            'date': directives.unchanged,
            'place': directives.unchanged,
            'contest_name': directives.unchanged,
            'contest_date': directives.unchanged,
            }

    def run(self):
        ret = '\n\n'
        if 'leftlogo' in self.options:
            ret += r'\renewcommand{\PDFleftlogo}{\includegraphics[height=0.9cm]{' + self.options['leftlogo'] + r'}}' + '\n'

        if 'rightlogo' in self.options:
            ret += r'\renewcommand{\PDFrightlogo}{\includegraphics[height=2.1cm,width=2cm]{' + self.options['rightlogo'] + r'}}' + '\n'

        if 'date' in self.options:
            ret += r'\renewcommand{\PDFdate}{' + self.options['date'] + r'}' + '\n'

        if 'contest_name' in self.options:
            ret += r'\renewcommand{\PDFcontestname}{' + self.options['contest_name'] + r'}' + '\n'

        if 'contest_date' in self.options:
            ret += r'\renewcommand{\PDFcontestdate}{' + self.options['contest_date'] + r'}' + '\n'

        if 'place' in self.options:
            ret += r'\renewcommand{\PDFplace}{' + self.options['place'] + r'}' + '\n'

        return [TexNode(value=ret)]


def setup(app):
    app.add_node(TexNode, latex=(visit_tex_node_tex, depart_tex_node), html=(visit_tex_node_other, depart_tex_node), text=(visit_tex_node_other, depart_tex_node))
    app.add_directive('pdfinfo', PdfInfoDirective)


#TODO: Make this irrelevant
#This is needed because of the bug in sphinx: application.py (the order of extensions loading)
def confToFile(filePath):
    config = open(filePath, 'w')
    for key, val in config_overrides.iteritems():
        if isinstance(val, str) or isinstance(val, (str, unicode)):
            raw = key + ' = "' + val.__str__() + '"\n'
        else:
            raw = key + ' = ' + val.__str__() + '\n'
        config.write(raw)
    config.close()


def render_sphinx(rest, oa_map):
    logging.debug(os.getcwd())
    if not rest.strip():
        to_delete = []
        for name in oa_map:
            oa = oa_map[name]
            if not oa.is_blob:
                continue
            if (name.startswith('_img_') or (name == '_pdf') or (name == '_html')):
                to_delete.append(name)
        for name in to_delete:
            del oa_map[name]
        if 'pdf' in oa_map:
            oa_map['_pdf'] = deepcopy(oa_map['pdf'])
            oa_map['_pdf'].name = '_pdf'
        return oa_map

    srcdir = mkdtemp()
    indexpath = os.path.join(srcdir, 'index.rst')

    rfile = open(indexpath, 'w')
    if isinstance(rest, unicode):
        rfile.write(rest.encode('utf-8'))
    else:
        rfile.write(rest)    
    rfile.close()

    to_delete = []
    for name in oa_map:
        oa = oa_map[name]
        if not oa.is_blob:
            continue
        if not (name.startswith('_img_') or (name == '_pdf') or (name == '_html')):
            reader = Blob.open(oa.value)
            dest = open(os.path.join(srcdir, name), 'w')
            dest.write(reader.read())
            reader.close()
            dest.close()
        else:
            to_delete.append(name)

    for name in to_delete:
        del oa_map[name]

    treedir = os.path.join(srcdir, '.doctrees')
    os.mkdir(treedir)
    confToFile(os.path.join(srcdir, 'conf.py'))

    builddir = os.path.join(srcdir, '_build')
    os.mkdir(builddir)

    try:
        app = Sphinx(srcdir, srcdir, builddir, treedir, 'html',
                confoverrides = config_overrides,
                freshenv = True,
                status=None,
                warning=None, 
                warningiserror=True)
        app.build(None, [indexpath])
    except SphinxError as e:
        raise SphinxException(error=unicode(e))
    except PycodeError:
        raise

    outfilepath = os.path.join(builddir, 'index.html')    
    assert os.path.exists(outfilepath)

    outfile = open(outfilepath, 'r')
    output = outfile.read()
    outfile.close()

    def mathrepl(matchobj):
        name = matchobj.group(1)
        newname = '_img_' + matchobj.group(1)
        src = open(os.path.join(srcdir, '_build', matchobj.group(0)), 'r')
        writer = Blob.create()
        writer.write(src.read())
        src.close()
        hash = writer.close()
        oa_map[newname] = AnonymousAttribute(is_blob=True, filename=newname, value=hash)
        return '_images/' + newname
    output = re.sub(r'_images\/math\/([a-zA-Z0-9]*\.png)', mathrepl, output)
    
    def linkrepl(matchobj):
        return '<a class="reference external" href="_images/' + matchobj.group(1) + '">'
    output = re.sub(r'<a class="reference external" href="([^"/]*)">', linkrepl, output)

    writer = Blob.create()
    writer.write(output)
    hash = writer.close()
    oa_map['_html'] = AnonymousAttribute(is_blob=True, filename='index.html', value=hash)

    if 'pdf' in oa_map:
        oa_map['_pdf'] = deepcopy(oa_map['pdf'])
        oa_map['_pdf'].name = '_pdf'
    else:
        pdfbuilddir = os.path.join(srcdir, '_buildpdf')
        os.mkdir(pdfbuilddir)
        
        for name in oa_map:
            oa = oa_map[name]
            if not oa.is_blob:
                continue
            if not (name.startswith('_img_') or (name == '_pdf') or (name == '_html')):
                reader = Blob.open(oa.value)
                dest = open(os.path.join(pdfbuilddir, name), 'w')
                dest.write(reader.read())
                reader.close()
                dest.close()

        confToFile(os.path.join(srcdir, 'conf.py'))

        try:
            app = Sphinx(srcdir, srcdir, pdfbuilddir, treedir, 'latex',
                    confoverrides = config_overrides,
                    freshenv = True,
                    status=None,
                    warning=None, 
                    warningiserror=True)
            app.build(None, [indexpath])
        except SphinxError as e:
            raise SphinxException(error=unicode(e))
        except PycodeError:
            raise

        texoutfilepath = os.path.join(pdfbuilddir, 'index.tex')    
        assert os.path.exists(texoutfilepath)

# save tex file for debug
#        outfile = open(texoutfilepath, 'r')
#        output = outfile.read()
#        outfile.close()

#        writer = Blob.create()
#        writer.write(output)
#        hash = writer.close()
#        oa_map['_tex'] = AnonymousAttribute(is_blob=True, filename='index.tex', value=hash)

        for filename in os.listdir(os.path.join(CORE_PATH, 'sphinx_templates', 'latex')):
            shutil.copy(os.path.join(CORE_PATH, 'sphinx_templates', 'latex', filename), pdfbuilddir)

# python 2.7
#        try:
#            subprocess.check_output(['pdflatex', 'index.tex'], cwd=pdfbuilddir, stderr=subprocess.STDOUT)
#        subprocess.check_output(['pdflatex', 'index.tex'], cwd=pdfbuilddir, stderr=subprocess.STDOUT)
#        except subprocess.CalledProcessError as e:
#            raise SphinxException(error='pdflatex ended with error code {0}:\n{1}'.format(e.returncode, e.output))

        # two times: pagerefs

        proc = subprocess.Popen(['pdflatex', '-halt-on-error', 'index.tex'], cwd=pdfbuilddir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise SphinxException(error='pdflatex ended with error code {0}:\n{1}'.format(proc.returncode, output))

        proc = subprocess.Popen(['pdflatex', 'index.tex'], cwd=pdfbuilddir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.communicate()[0]
        if proc.returncode != 0:
            raise SphinxException(error='pdflatex ended with error code {0}:\n{1}'.format(proc.returncode, output))

        pdfoutfilepath = os.path.join(pdfbuilddir, 'index.pdf')    
        assert os.path.exists(pdfoutfilepath)

        outfile = open(pdfoutfilepath, 'rb')
        output = outfile.read()
        outfile.close()

        writer = Blob.create()
        writer.write(output)
        hash = writer.close()
        oa_map['_pdf'] = AnonymousAttribute(is_blob=True, filename='index.pdf', value=hash)

    shutil.rmtree(srcdir, ignore_errors=True)

    return oa_map
