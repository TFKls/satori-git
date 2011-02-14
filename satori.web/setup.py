# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.web',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'flup',
        'setuptools',
        'Thrift',
        'satori.client.common',
        'Sphinx',
    ],
    entry_points='''
        [console_scripts]
	    satori.web.manage = satori.web:manage
    ''',
)
