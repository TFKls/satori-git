# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.client.web',
    packages=find_packages(),
    namespace_packages=[
        'satori',
        'satori.client',
    ],
    install_requires=[
        'flup',
        'setuptools',
        'Thrift',
        'satori.client.common',
    ],
    entry_points='''
        [console_scripts]
	    satori.client.web.manage = satori.client.web:manage
    ''',
)
