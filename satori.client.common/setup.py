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
)
