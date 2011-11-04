# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.client.common',
    packages=find_packages(),
    namespace_packages=[
        'satori',
        'satori.client',
    ],
    install_requires=[
        'setuptools',
        'Thrift',
        'satori.ars',
        'satori.objects',
    ],
#    entry_points='''
#        [console_scripts]
#        satori.client.console = satori.client.common:start_console
#        satori.client.localconsole = satori.client.common:start_local_console
#    ''',
)
