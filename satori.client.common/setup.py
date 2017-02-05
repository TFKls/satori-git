# vim:ts=4:sts=4:sw=4:expandtab
from setuptools import setup, find_packages

setup(
    name='satori.client.common',
    version='0.1',
    description='Satori Testing System client library',
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
        'satori.client',
    ],
    install_requires=[
        'setuptools',
        'Thrift < 0.10',
        'satori.ars',
        'satori.objects',
    ],
#    entry_points='''
#        [console_scripts]
#        satori.client.console = satori.client.common:start_console
#        satori.client.localconsole = satori.client.common:start_local_console
#    ''',
)
