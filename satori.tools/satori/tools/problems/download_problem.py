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

from satori.tools.problems.common import copy_file, slugify


def get_problem(problem_name):
    problems = Problem.filter(ProblemStruct(name=problem_name))
    assert len(problems) <= 1, 'Problem names are declared to be unique'
    if len(problems) == 0:
        raise RuntimeError('Problem with a given name not found')
    else:
        return problems[0]


def create_suite_json(suite):
    suite_json = {}
    if not suite.name:
        raise RuntimeError('Problem has anonymous test suite')
    suite_json['name'] = suite.name
    suite_json['dispatcher'] = suite.dispatcher
    suite_json['reporter'] = suite.reporter
    for param in suite.params_get_list():
        suite_json[param.name] = param.value
    suite_json['tests'] = [test.name for test in suite.get_tests()]
    return suite_json


def create_test_json(test):
    test_json = {}
    if not test.name:
        raise RuntimeError('Problem has anonymous test suite')
    test_json['name'] = test.name
    for data in test.data_get_list():
        if data.is_blob:
            test_json[data.name] = {
                'filename': data.filename,
                'hash': data.value
            }
        else:
            test_json[data.name] = data.value
    return test_json


def has_duplicates(names):
    return len(names) > len(set(names))


def store_problem(problem_json, tests_json):
    if has_duplicates([slugify(test['name']) for test in tests_json]):
        raise RuntimeError('Slugified test names\' are not unique')
    problem_dir = slugify(problem_json['name'])
    os.mkdir(problem_dir)
    problem_file = open(os.path.join(problem_dir, 'problem.json'), 'w')
    json.dump(problem_json, problem_file, indent=4)
    problem_file.close()
    for test_json in tests_json:
        test_dir = slugify(test_json['name'])
        os.mkdir(os.path.join(problem_dir, test_dir))
        for (key, val) in test_json.items():
            if type(val) == dict:  # blob
                remote_blob = Blob.open(val['hash'])
                local_blob = open(
                        os.path.join(problem_dir, test_dir, val['filename']),
                        'w')
                print 'Downloading blob', val['filename'] + ',',
                print 'size =', remote_blob.length, 'bytes' + '...',
                sys.stdout.flush()
                copy_file(remote_blob, local_blob)    
                print 'done'
                remote_blob.close()
                local_blob.close()
                test_json[key] = val['filename']
        test_file = open(os.path.join(problem_dir, test_dir, 'test.json'), 'w')
        json.dump(test_json, test_file, indent=4)
        test_file.close()
        # TODO: check blob names are unique
        # TODO: avoid fetching the same blob twice


def download_problem(opts):
    problem_name = opts.PROBLEM_NAME
    problem = get_problem(problem_name)
    
    problem_json = {}
    problem_json['name'] = problem.name
    problem_json['description'] = problem.description
    
    suites = TestSuite.filter(TestSuiteStruct(problem=problem))
    problem_json['suites'] = [create_suite_json(suite) for suite in suites]

    tests = Test.filter(TestStruct(problem=problem))
    tests_json = [create_test_json(test) for test in tests]

    store_problem(problem_json, tests_json)

