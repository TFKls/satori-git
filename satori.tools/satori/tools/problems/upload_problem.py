# vim:ts=4:sts=4:sw=4:et
import argparse
import logging
import os
import os.path
import shutil
import sys
import time
import yaml

from satori.client.common import want_import
want_import(globals(), '*')
from satori.tools import auth_setup, catch_exceptions, config, options, setup
from satori.tools.params import parser_from_xml

from satori.tools.problems.common import Dirs, discover_tests, make_oa_map, make_test_data, upload_blob


def upload_problem(opts):
    problem_dir = opts.PROBLEM if opts.PROBLEM else os.getcwd()
    
    with open(os.path.join(problem_dir, 'problem.yaml')) as problem_yaml_file:
        problem_yaml = yaml.safe_load(problem_yaml_file)
    if type(problem_yaml) != dict:
        raise RuntimeError('Problem YAML must be an object')
    if 'name' not in problem_yaml:
        raise RuntimeError('Problem must have a name')
    problem_name = problem_yaml['name']
    problem_description = problem_yaml.get('description', '')

    if len(Problem.filter(ProblemStruct(name=problem_name))):
        raise RuntimeError('Updating exisitng problems is not yet supported')

    problem = Problem.create(ProblemStruct(
                name=problem_name, description=problem_description))

    local_tests = discover_tests(problem_dir)
    remote_tests = {}
    for test_dir in local_tests.values():
        dirs = Dirs(problem_dir, test_dir)
        test_data = make_test_data(dirs)
        remote_test = Test.create(
                    TestStruct(
                            problem=problem,
                            name=test_data['name'].value,
                            description=test_data['description'].value),
                    test_data)
        remote_tests[remote_test.name] = remote_test

    suites_yaml = problem_yaml.get('suites', [])
    if type(suites_yaml) != list:
        raise RuntimeError('Suites YAML must be a list')
    for suite_yaml in suites_yaml:
        if type(suite_yaml) != dict:
            raise RuntimeError('Suite YAML must be an object')
        for key in ('name', 'dispatcher', 'reporter',):
            if key not in suite_yaml:
                raise RuntimeError('Suite must have a ' + key)
        suite_name = suite_yaml['name']
        suite_description = suite_yaml.get('description', '')
        suite_dispatcher = suite_yaml['dispatcher']
        suite_reporter = suite_yaml['reporter']
        if 'accumulators' in suite_yaml:
            raise RuntimeError('Accumulators are not yet supported')
        reporters = Global.get_reporters()
        if suite_reporter not in reporters:
            raise RuntimeError('Reporter with a given name not found')
        parsed_reporter = parser_from_xml(reporters[suite_reporter])
        reporter_params_yaml = dict(
                [(key.split('.')[1], val) for (key, val)
                        in suite_yaml.items()
                                if key.split('.')[0] == suite_reporter])
        reporter_params = dict(
                [(suite_reporter + '.' + key, val) for (key, val) in
                        make_oa_map(
                                parsed_reporter, reporter_params_yaml, None).items()])
        tests_in_suite_yaml = suite_yaml.get('tests', [])
        tests_in_suite = []
        for test_in_suite_yaml in tests_in_suite_yaml:
            if test_in_suite_yaml not in remote_tests:
                raise RuntimeError(str(test_in_suite_yaml) + ' not found')
            tests_in_suite.append(remote_tests[test_in_suite_yaml])
        TestSuite.create(
                TestSuiteStruct(
                        problem=problem,
                        name=suite_name,
                        description=suite_description,
                        dispatcher=suite_dispatcher,
                        reporter=suite_reporter,
                        accumulators=''),
                reporter_params,
                tests_in_suite,
                [{} for _ in tests_in_suite])

