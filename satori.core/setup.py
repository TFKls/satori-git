# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.core',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'pycrypto',
        'python-openid',
        'python-memcached',
        'setuptools',
        'Django >= 1.3',
        'egenix-mx-base',
        'psycopg2',
        'Thrift',
        'satori.ars',
        'satori.events',
        'satori.objects',
        'satori.tools',
        'setproctitle',
        'cherrypy >= 3.2',
        'ipaddr',
        'gdata',
    ],
    entry_points='''
        [console_scripts]
        satori.core = satori.core:manage
    ''',
)
