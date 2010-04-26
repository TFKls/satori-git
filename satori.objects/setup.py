# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='Satori',
    packages=find_packages(),
    install_requires=[
        'Django >= 1.1.1',
        'psycopg2',
        'Genshi',
        'docutils',
        'Pygments',
        'Thrift',
        'pylint',
    ]
)
