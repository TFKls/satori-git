# vim:ts=4:sts=4:sw=4:et
import argparse
import glob
import json
import logging
import os
import os.path
import shutil
import sys
import time

from satori.client.common import want_import
want_import(globals(), '*')
from satori.tools import auth_setup, catch_exceptions, config, options, setup
from satori.tools.params import parser_from_xml

from satori.tools.problems.common import upload_blob
from satori.tools.problems.download_problem import download_problem
from satori.tools.problems.temporary_submit import temporary_submit

#############################     Entry point     #############################

@catch_exceptions
def main():
    subparsers = options.add_subparsers()
    
    list_dispatchers_parser = subparsers.add_parser('dispatchers')
    list_dispatchers_parser.set_defaults(command=list_dispatchers)

    list_reporters_parser = subparsers.add_parser('reporters')
    list_reporters_parser.set_defaults(command=list_reporters)

    list_reporter_params_parser = subparsers.add_parser('reporter')
    list_reporter_params_parser.set_defaults(command=list_reporter_params)
    list_reporter_params_parser.add_argument('REPORTER_NAME')

    list_problems_parser = subparsers.add_parser('list')
    list_problems_parser.set_defaults(command=list_problems)

    download_problem_parser = subparsers.add_parser('download')
    download_problem_parser.set_defaults(command=download_problem)
    download_problem_parser.add_argument('PROBLEM_NAME')
    
    temporary_submit_parser = subparsers.add_parser('test')
    temporary_submit_parser.set_defaults(command=temporary_submit)
    temporary_submit_parser.add_argument('TEST')
    temporary_submit_parser.add_argument('SOLUTION')

    # TODO
    # upload_problem_parser = subparsers.add_parser('upload')
    
    opts = setup(logging.CRITICAL)
    opts.command(opts)

#############################     Dispatchers     #############################

def list_dispatchers(_):
    for name in sorted(Global.get_dispatchers().keys()):
        print name

#############################     Reporters       #############################

def list_reporters(_):
    for name in sorted(Global.get_reporters().keys()):
        print name

def list_reporter_params(opts):
    reporter_name = opts.REPORTER_NAME
    reporters = Global.get_reporters()
    if reporter_name not in reporters:
        raise RuntimeError('Reporter with a given name not found')
    parsed_reporter = parser_from_xml(reporters[reporter_name])
    if parsed_reporter and parsed_reporter.params:
        params = parsed_reporter.params
        padding = max([len(param.name) for param in params])
        for param in params:
            print param.name.ljust(padding),
            print param.description + ',', 
            print ('required' if param.required else 'optional') + ',',
            print 'default=' + str(param.default)
    else:
        print reporter_name, 'has no params'

#############################    List problems    #############################

def list_problems(_):
    problem_names = [problem.name for problem in Problem.filter()]
    for name in sorted(problem_names):
        print name

