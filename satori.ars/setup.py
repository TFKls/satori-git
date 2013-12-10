# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(
    name='satori.ars',
    version='0.1',
    description='Satori Testing System abstract rpc scheme',
    author='Satori Project',
    author_email='satori@tcs.uj.edu.pl',
    url='https://bitbucket.org/satoriproject/satori',
    license='The MIT License',
    classifiers=[
        'Intended Audience :: Education',
        'Topic :: Education :: Testing',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    packages=find_packages(),
    namespace_packages=[
        'satori',
    ],
    install_requires=[
        'setuptools',
        'ply',
        'satori.objects',
        'blist',
    ],
)
