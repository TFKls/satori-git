# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.tools',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'satori.client.common',
    ],
    entry_points='''
        [console_scripts]
        satori.athina_import = satori.tools.athina:athina_import
        satori.console = satori.tools.console:main
    ''',
)
