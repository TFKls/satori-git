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
    name='satori.core',
    version='0.1',
    description='Satori Testing System core server',
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
        'pycrypto == 2.3',
        'pyopenssl',
        'python-openid',
        'python-memcached',
        'setuptools',
        'Django == 1.4',
        'egenix-mx-base',
        'psycopg2',
        'Thrift',
        'satori.ars',
        'satori.events',
        'satori.objects',
        'satori.tools',
        'setproctitle',
        'Twisted',
        'uwsgi >= 1.3'
        'pyopenssl',
        'ipaddr',
        'gdata',
        'pyyaml',
        'sphinx',
    ],
    entry_points='''
        [console_scripts]
        satori.core = satori.core:manage
    ''',
    package_data={
        'satori.core': ['entities/*.py', 'judges/*.py'] + find_files('satori/core/sphinx_templates', 'sphinx_templates/'),
    },
)
