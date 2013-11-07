# vim:ts=4:sts=4:sw=4:et
import os
import sys
import time

from satori.client.common import want_import
want_import(globals(), '*')

from satori.tools.problems.common import Dirs, discover_tests, make_test_data, upload_blob


def _temporary_submit_internal(problem_dir, test_dir, submit_file_path,
                               override_time=None):
    dirs = Dirs(problem_dir, test_dir)
    test_data = make_test_data(dirs)
    if override_time is not None and 'time' in test_data:
        test_data['_original_time'] = test_data['time']
        test_data['time'] = AnonymousAttribute(is_blob=False, value=override_time)
    submit_data = {'content': upload_blob(submit_file_path)}
    submit = TemporarySubmit.create(test_data, submit_data)
    print 'Testing %s on %s, temporary submit id: %d' % (
            submit_data['content'].filename,
            test_data['name'].value,
            submit.id)
    return submit


def _prettyprint_table(table):
    widths = [max(map(len, column)) for column in zip(*table)]
    for row in table:
        row = [elem.ljust(width) for (elem, width) in zip(row, widths)]
        print '  '.join(row)


def _results_header():
    return ['solution', 'test', 'status', 'time', 'temporary submit id']


def _get_from_map(attr_map, attr):
    if attr in attr_map:
        return str(attr_map[attr].value)
    else:
        return '?'


def _submit_to_results_row(submit):
    test_map = submit.test_data_get_map()
    result_map = submit.result_get_map()
    result_row = []
    result_row.append(submit.submit_data_get_map()['content'].filename)
    result_row.append(_get_from_map(test_map, 'name'))
    result_row.append(_get_from_map(result_map, 'status'))
    if '_original_time' in test_map:
        result_row.append('%s / %s (%s)' % (
                _get_from_map(result_map, 'execute_time_cpu'),
                _get_from_map(test_map, '_original_time'),
                _get_from_map(test_map, 'time')))
    else:
        result_row.append('%s / %s' % (
                _get_from_map(result_map, 'execute_time_cpu'),
                _get_from_map(test_map, 'time')))
    result_row.append(str(submit.id))
    return result_row


def _wait_for_results(submits):
    waiting_start = time.time()
    total = len(submits)
    print 'Waiting for results, %d/%d done' % (0, total),
    sys.stdout.flush()
    last_reported = 0
    while True:
        done = 0
        for submit in submits:
            if submit.result_get_list():
                done += 1
        if done >= total:
            break
        if done > last_reported:
            print
            print 'Waiting for results, %d/%d done' % (done, total),
            sys.stdout.flush()
            last_reported = done
        time.sleep(2)
        print '.',
        sys.stdout.flush()
    waiting_time = time.time() - waiting_start
    print
    print 'You had to wait %ds' % int(round(waiting_time))


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
                    problem_dir, test_dir, submit_file_path, opts.time)
            submits.append(submit)

    _wait_for_results(submits)
    _prettyprint_table(
            [_results_header()] + map(_submit_to_results_row, submits))


def _print_bold_caption(caption):
    print '\033[1m' + caption + ':' + '\033[0m',


def temporary_submit_result(opts):
    submit = TemporarySubmit.filter(TemporarySubmitStruct(id=int(opts.TSID)))
    if not submit:
        raise RuntimeError('Unknown temporary submit id')
    submit = submit[0]
    
    _print_bold_caption('solution')
    print submit.submit_data_get_map()['content'].filename
    _print_bold_caption('test')
    print submit.test_data_get_map()['name'].value

    result = submit.result_get_list()
    if not result:
        print 'no results available yet'
        return
    for attr in result:
        _print_bold_caption(attr.name)
        if attr.is_blob:
            print
            content = submit.result_get_blob(attr.name).read(4096)
            content = content.rstrip('\n')
            if not content:
                continue
            print content
        else:
            print attr.value
