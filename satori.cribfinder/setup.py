# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.cribfinder',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'satori.client.common',
        'satori.tools',
    ],
    entry_points='''
        [console_scripts]
        satori.cribfinder_init = satori.cribfinder:cribfinder_init
    ''',
)