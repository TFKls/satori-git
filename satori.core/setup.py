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
        'Django >= 1.1.1',
        'egenix-mx-base',
        'psycopg2',
        'Thrift',
        'satori.ars',
        'satori.events',
        'satori.objects',
        'setproctitle',
        'cherrypy',
        'ipaddr',
    ],
    entry_points='''
        [console_scripts]
        satori.idl = satori.core:export_thrift
        satori.server = satori.core:start_server
        satori.server.manage = satori.core:manage
    ''',
)
