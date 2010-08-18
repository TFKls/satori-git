# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.judge',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'python-prctl',
        'python-unshare',
        'pyyaml',
    ],
    entry_points='''
        [console_scripts]
        satori.judge = satori.judge:start_judge
    ''',
)
