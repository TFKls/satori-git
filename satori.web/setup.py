# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages
from distutils.util import convert_path
import os

def find_files(where='.', prefix=''):
    out = []
    stack=[(convert_path(where), prefix)]
    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if name != '..' and name != '.' and os.path.isdir(fn):
                stack.append((fn,prefix+name+'/'))
            elif os.path.isfile(fn):
                out.append(prefix+name); 
    return out

setup(
    name='satori.web',
    version='0.1',
    description='Satori Testing System web interface',
    author='Satori Project',
    author_email='satori@tcs.uj.edu.pl',
    url='https://bitbucket.org/satoriproject/satori',
    license='The MIT License',
    classifiers=[
        'Intended Audience :: Education',
        'Topic :: Education :: Testing',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'six',
        'Django == 1.4',
        'flup',
        'setuptools',
        'Thrift',
        'satori.client.common',
        'satori.tools',
        'Sphinx',
        'xstatic-mathjax',
    ],
    entry_points='''
        [console_scripts]
	    satori.web.manage = satori.web:manage
    ''',
    package_data={
        'satori.web': find_files('satori/web/templates', 'templates/') + find_files('satori/web/files', 'files/'),
    },
)
