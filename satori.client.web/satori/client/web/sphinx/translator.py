MYPREAMBLE = r'''
\\pagenumbering{arabic}
\definecolor{TitleColor}{rgb}{0,0,0}
\definecolor{InnerLinkColor}{rgb}{0,0,0}
'''

import re
import sys, os, shutil
from tempfile import mkdtemp
from sphinx.application import Sphinx
from sphinx.errors import PycodeError, SphinxError

TRANS_PATH = os.path.abspath(os.path.split(__file__)[0])

config_overrides = {
    'extensions' : ['sphinx.ext.pngmath','sphinx.ext.graphviz',],
    'templates_path' : [],
    'source_suffix' : '.rst',
    'master_doc' : 'index',
    'project' : u'',
    'copyright': u'',
    'version' : '1',
    'release' : '1',
    'exclude_patterns' : ['_build'],
    'pygments_style' : 'sphinx',

    'html_theme' : 'default',
    'html_theme_path' : [os.path.join(TRANS_PATH, 'templates')],
    'html_static_path' : ['_static'],
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

def rendertask(rststring, discpath, mathpath):
    tmpdir = mkdtemp()

    indexpath = os.path.join(tmpdir,'index.rst')
    tfile = open(indexpath,'w')
    if isinstance(rststring, unicode):
        tfile.write(rststring.encode('utf-8'))
    else:
        tfile.write(rststring)    
    tfile.close()

    srcdir = tmpdir
    builddir = os.path.join(tmpdir, '_build')
    treedir = os.path.join(tmpdir, '.doctrees')
    os.mkdir(builddir)
    os.mkdir(treedir)

    templatesdir = os.path.join(TRANS_PATH, 'templates')

    config_overrides['templates_path'].append(templatesdir)
    confToFile(os.path.join(tmpdir,'conf.py'))

    try:
        app = Sphinx(srcdir, srcdir, builddir, treedir, 'html',
                confoverrides = config_overrides,
                freshenv = True,
                status=None,
                warning=None, 
                warningiserror=True)
        app.build(None, [indexpath])
    except SphinxError:
        raise
    except PycodeError:
        raise

    outfilepath = os.path.join(builddir, 'index.html')    
    assert os.path.exists(outfilepath)

    outfile = open(outfilepath,'r')
    output = outfile.read()
    output = unicode(output,'utf-8')
    outfile.close()

    def mathrepl(matchobj):
        newimgpath = os.path.join(mathpath, matchobj.group(1))
        filepath = os.path.join(discpath, matchobj.group(1))
        shutil.copyfile(os.path.join(tmpdir, '_build/' + matchobj.group(0)), filepath)
        return newimgpath
    output = re.sub(r'_images\/math\/([a-zA-Z0-9]*\.png)', mathrepl, output)

    shutil.rmtree(tmpdir, ignore_errors=True)
    return output
