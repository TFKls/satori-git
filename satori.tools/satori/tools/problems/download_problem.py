from six import print_
# vim:ts=4:sts=4:sw=4:et
import os
import os.path
import sys
import yaml

from satori.client.common import want_import
want_import(globals(), '*')

from satori.tools.problems.common import copy_file, slugify


def get_problem(problem_name):
    problems = Problem.filter(ProblemStruct(name=problem_name))
    assert len(problems) <= 1, 'Problem names are declared to be unique'
    if len(problems) == 0:
        raise RuntimeError('Problem with a given name not found')
    else:
        return problems[0]


def create_suite_yaml(suite):
    suite_yaml = {}
    if not suite.name:
        raise RuntimeError('Problem has anonymous test suite')
    suite_yaml['name'] = suite.name
    suite_yaml['dispatcher'] = suite.dispatcher
    suite_yaml['reporter'] = suite.reporter
    for param in suite.params_get_list():
        suite_yaml[param.name] = param.value
    suite_yaml['tests'] = [test.name for test in suite.get_tests()]
    return suite_yaml


def create_test_yaml(test):
    test_yaml = {}
    if not test.name:
        raise RuntimeError('Problem has anonymous test suite')
    test_yaml['name'] = test.name
    for data in test.data_get_list():
        if data.is_blob:
            test_yaml[data.name] = {
                'filename': data.filename,
                'hash': data.value
            }
        else:
            test_yaml[data.name] = data.value
    return test_yaml


def has_duplicates(names):
    return len(names) > len(set(names))


def valid_file_name(name):
    return name != '.' and name != '..' and '/' not in name

def store_problem(problem_yaml, tests_yaml):
    for test in tests_yaml:
        if not valid_file_name(test['name']):
            raise RuntimeError('Cannot store problem, one of test names is not a valid file name')
    problem_dir = slugify(problem_yaml['name'])
    os.mkdir(problem_dir)
    problem_file = open(os.path.join(problem_dir, 'problem.yaml'), 'w')
    yaml.safe_dump(problem_yaml, stream=problem_file, indent=2)
    problem_file.close()
    for test_yaml in tests_yaml:
        test_dir = test_yaml['name']
        os.mkdir(os.path.join(problem_dir, test_dir))
        for (key, val) in test_yaml.items():
            if type(val) == dict:  # blob
                remote_blob = Blob.open(val['hash'])
                local_blob = open(
                        os.path.join(problem_dir, test_dir, val['filename']),
                        'w')
                print_('Downloading blob', val['filename'] + ',', end="")
                print_('size =', remote_blob.length, 'bytes' + '...', end="")
                sys.stdout.flush()
                copy_file(remote_blob, local_blob)    
                print_('done')
                remote_blob.close()
                local_blob.close()
                test_yaml[key] = val['filename']
        test_file = open(os.path.join(problem_dir, test_dir, 'test.yaml'), 'w')
        yaml.safe_dump(test_yaml, stream=test_file, indent=2,
                       default_flow_style=False)
        test_file.close()
        # TODO: check blob names are unique
        # TODO: avoid fetching the same blob twice


def download_problem(opts):
    problem_name = opts.PROBLEM_NAME
    problem = get_problem(problem_name)
    
    problem_yaml = {}
    problem_yaml['name'] = problem.name
    problem_yaml['description'] = problem.description
    
    suites = TestSuite.filter(TestSuiteStruct(problem=problem))
    problem_yaml['suites'] = [create_suite_yaml(suite) for suite in suites]

    tests = Test.filter(TestStruct(problem=problem))
    tests_yaml = [create_test_yaml(test) for test in tests]

    store_problem(problem_yaml, tests_yaml)

