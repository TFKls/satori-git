# vim:ts=4:sts=4:sw=4:et
import argparse
import glob
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

from satori.tools.problems.common import Dirs, discover_tests, make_test_data, upload_blob


def _temporary_submit_internal(problem_dir, test_dir, submit_file_path):
    dirs = Dirs(problem_dir, test_dir)
    test_data = make_test_data(dirs)
    submit_data = {'content': upload_blob(submit_file_path)}
    submit = TemporarySubmit.create(test_data, submit_data)
    return submit


def _print_temporary_submit_result(submit):
    print 'solution', ':', submit.submit_data_get_map()['content'].filename
    print 'test', ':', submit.test_data_get_map()['name'].value
    print 'temporary_submit_id', ':', submit.id
    blobs = []
    for attr in submit.result_get_list():
        if attr.is_blob:
            blobs.append(attr.name)
        else:
            print attr.name, ':', attr.value
    print 'blobs', ':', ', '.join(blobs) 


def temporary_submit(opts):
    if ':' not in opts.TEST:
        raise RuntimeError('TEST must be of form PROBLEM_DIR:TEST_NAME')
    problem_dir, test_name = opts.TEST.split(':', 1)
    if not problem_dir:
        problem_dir = os.getcwd()
    tests = discover_tests(problem_dir)
    if test_name and test_name not in tests:
        raise RuntimeError('Unknown test name')
    test_dirs = [tests[test_name]] if test_name else tests.values()
    
    submits = []
    for submit_file_path in opts.SOLUTION:
        for test_dir in test_dirs:
            submit = _temporary_submit_internal(
                    problem_dir, test_dir, submit_file_path)
            submits.append(submit)

    print 'Waiting for results . . .',
    sys.stdout.flush()
    while True:
        time.sleep(5)
        done = True
        for submit in submits:
            if not submit.result_get_list():
                done = False
                break
        if done:
            print
            for submit in submits:
                _print_temporary_submit_result(submit)
            break
        print '.',
        sys.stdout.flush()
       
