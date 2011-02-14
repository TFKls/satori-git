# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(name='satori.judge',
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'python-unshare',
        'pyyaml',
        'satori.client.common',
        'satori.tools',
    ],
    entry_points='''
        [console_scripts]
        satori.judge_init = satori.judge:judge_init
    ''',
)
