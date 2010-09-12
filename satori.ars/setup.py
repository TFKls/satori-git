# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.ars',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'ply',
        'satori.objects',
        'blist',
    ]
)
