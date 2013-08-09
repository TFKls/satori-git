# vim:ts=4:sts=4:sw=4:et
import argparse
import logging
import glob
import os
import os.path
import sys

import json
import shutil
import time

from utils import slugify

from satori.client.common import want_import
from satori.tools import config, options, setup, auth_setup, catch_exceptions
from satori.tools.params import parser_from_xml
want_import(globals(), '*')

#############################     Entry point     #############################

#@catch_exceptions
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

    fetch_problem_parser = subparsers.add_parser('fetch')
    fetch_problem_parser.set_defaults(command=fetch_problem)
    fetch_problem_parser.add_argument('PROBLEM_NAME')
    
    temporary_submit_parser = subparsers.add_parser('test')
    temporary_submit_parser.set_defaults(command=temporary_submit)
    temporary_submit_parser.add_argument('TEST')
    temporary_submit_parser.add_argument('SOLUTION')

    push_problem_parser = subparsers.add_parser('push')
    
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

#############################    Fetch problem    #############################

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
                BUF_SIZ = 4096
                while True:
                    buf = remote_blob.read(BUF_SIZ)
                    if not buf:
                        break
                    local_blob.write(buf)
                print 'done'
                remote_blob.close()
                local_blob.close()
                test_json[key] = val['filename']
        test_file = open(os.path.join(problem_dir, test_dir, 'test.json'), 'w')
        json.dump(test_json, test_file, indent=4)
        test_file.close()
        # TODO: check blob names are unique
        # TODO: avoid fetching the same blob twice

def fetch_problem(opts):
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

#############################     Temp submit     #############################

def parse_path(dirs, path):
    assert 'problem' in dirs and 'test' in dirs
    if path[:1] == "/":  # 'absolute' path 
        return os.path.join(dirs['problem'], path[1:])
    else:  # relative path
        return os.path.join(dirs['test'], path)


def make_blob(blob_path, dirs=None):
    if dirs:
        blob_path = parse_path(dirs, blob_path)
    with open(blob_path) as blob_file:
        blob_size = os.path.getsize(blob_path)
        blob = Blob.create(blob_size)
        print 'Uploading blob', os.path.basename(blob_path) + ',',
        print 'size =', blob_size, 'bytes' + '...',
        sys.stdout.flush()
        blob.write(blob_file.read())  # TODO: copying buffer
        print 'done'
    blob_hash = blob.close()
    blob_name = os.path.basename(blob_path)
    return AnonymousAttribute(is_blob=True, value=blob_hash, filename=blob_name)


def make_oa_map(params_parser, json_data, dirs):
    if not params_parser or not params_parser.params:
        return {}
    oa_map = {}
    for param in params_parser.params:
        if param.name in json_data:
            if param.type_.name() == 'blob':
                oa_map[param.name] = make_blob(json_data[param.name], dirs)
            else:
                oa_map[param.name] = AnonymousAttribute(is_blob=False, value=json_data[param.name])
        else:
            if param.required and param.default is None:
                raise RuntimeError(
                        'Required param %s not specified' % param.name)
    return oa_map


def open_test(test_json_fname):
    with open(test_json_fname) as test_json_file:
        test_json = json.load(test_json_file)
    if type(test_json) != dict:
        raise RuntimeError('Test JSON must be an object')
    if 'name' not in test_json:
        raise RuntimeError('Test must have a name')
    return test_json


def make_test_data(dirs):
    test_json = open_test(os.path.join(dirs['test'], 'test.json'))
    test_name = test_json['name']
    # TODO: test description

    if 'judge' not in test_json:
        raise RuntimeError('No judge specified')

    judge_path = parse_path(dirs, test_json['judge'])
    with open(judge_path) as judge_file:
        judge_content = judge_file.read()

    judge_params = parser_from_xml(judge_content)
    test_data = make_oa_map(judge_params, test_json, dirs)
    test_data['name'] = AnonymousAttribute(is_blob=False, value=test_name)
    test_data['judge'] = make_blob(judge_path)

    return test_data


def discover_tests(problem_dir):
    # TODO: fail if problem_dir does not contain problem.json file.
    tests = []
    for fname in glob.glob(os.path.join(problem_dir, '*', 'test.json')):
        test_json = open_test(fname)
        tests.append((test_json['name'], os.path.dirname(fname)))
    return dict(tests)


def get_temporary_submit_result(submit_id):
    submits = TemporarySubmit.filter(TemporarySubmitStruct(id=submit_id))
    if not submits:
        return None
    result = submits[0].result_get_list()
    return result if result else None


def print_temporary_submit_result(result):
    blobs = []
    for attr in result:
        if attr.is_blob:
            blobs.append(attr.name)
        else:
            print attr.name, ':', attr.value
    print 'blobs', ':', ', '.join(blobs) 


def temporary_submit(opts):
    if ':' not in opts.TEST:
        raise RuntimeError('TEST must be of form PROBLEM_DIR:TEST_NAME')
    problem_dir, test_name = opts.TEST.split(':', 1)
    if not test_name:
        raise RuntimeError(
                'Specify a test name. Running all tests is not yet supported')
    if not problem_dir:
        problem_dir = os.getcwd()
    tests = discover_tests(problem_dir)
    if test_name not in tests:
        raise RuntimeError('Unknown test name')
    dirs = { 'test': tests[test_name], 'problem': problem_dir }
    submit_file_path = opts.SOLUTION

    test_data = make_test_data(dirs)
    submit_data = {'content': make_blob(submit_file_path)}

    submit = TemporarySubmit.create(test_data, submit_data)
    submit_id = submit.id
    print 'Temporary submit id:', submit_id

    print 'Waiting for results...'
    while True:
        time.sleep(2)
        result = get_temporary_submit_result(submit_id)
        if result:
            print_temporary_submit_result(result)
            break
        print "No results yet"
       
