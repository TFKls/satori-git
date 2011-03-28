
SphinxException = DefineException('SphinxException', 'Sphinx error: {error}', [('error', unicode, False)])

MYPREAMBLE = r'''
\\pagenumbering{arabic}
\definecolor{TitleColor}{rgb}{0,0,0}
\definecolor{InnerLinkColor}{rgb}{0,0,0}
'''

PREAMBLE = r'''
\usepackage{amsmath}
\usepackage{polski}
'''

import re
import sys, os, shutil
from tempfile import mkdtemp
from sphinx.application import Sphinx
from sphinx.errors import PycodeError, SphinxError

CORE_PATH = os.path.abspath(os.path.split(__file__)[0])

config_overrides = {
    'extensions' : ['sphinx.ext.pngmath','sphinx.ext.graphviz',],
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
    'pngmath_latex_preamble' : PREAMBLE,

#    'html_theme' : 'default',
#    'html_theme_path' : [os.path.join(CORE_PATH, 'sphinx_templates')],
#    'html_static_path' : ['_static'],
    'htmlhelp_basename' : '',

#    'latex_documents' :  [('index','index.tex','','','manual')], #[('index', 'tex file', u'Project name', u'Authors', 'manual')]
}


#sys.path.append(os.path.abspath('builders'))
#sys.path.append(os.path.abspath('static'))

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
            if name != '_pdf':
                to_delete.append(name)

    for name in to_delete:
        del oa_map[name]

    builddir = os.path.join(srcdir, '_build')
    treedir = os.path.join(srcdir, '.doctrees')
    os.mkdir(builddir)
    os.mkdir(treedir)

    confToFile(os.path.join(srcdir, 'conf.py'))

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

    shutil.rmtree(srcdir, ignore_errors=True)

    return oa_map

