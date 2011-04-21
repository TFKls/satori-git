# vim:ts=4:sts=4:sw=4:expandtab

import os
import re
import shutil
import string
import sys
import traceback
from datetime import datetime, timedelta

from satori.client.common import want_import
want_import(globals(), '*')

def seconds(time):
    return float(time.microseconds + (time.seconds + time.days * 24 * 3600) * 10**6) / 10**6

class Creator(object):
    def __init__(self, class_name, **kwargs):
        self._name = class_name
        self._class = globals()[self._name]
        self._struct = globals()[self._name+'Struct']
        self._search = kwargs
        self._create = kwargs
        self._function = 'create'
        self._additional = {}

    def set_fields(self, **kwargs):
        self._create = kwargs
        return self

    def fields(self, **kwargs):
        self._create.update(kwargs)
        return self

    def set_additional(self, **kwargs):
        self._additional = kwargs
        return self

    def additional(self, **kwargs):
        self._additional.update(kwargs)
        return self

    def function(self, f):
        self._function = f
        return self

    def search(self):
        a = self._class.filter(self._struct(**self._search))
        if len(a):
            return a[0]
        return None

    def create(self):
        func = getattr(self._class, self._function)
        return func(self._struct(**self._create), **self._additional)

    def __call__(self):
        a = self.search()
        if a is None:
            a = self.create()
        return a

def athina_import():
    import os,sys,getpass
    from satori.tools import options, setup
    options.add_option('-N', '--name',
        default='',
        action='store',
        type='string',
        help='Contest name')
    options.add_option('-E', '--environment',
        default='default',
        action='store',
        type='string',
        help='Test environment name')
    (options, args) = setup()
    if len(args) != 1:
        parser.error('incorrect number of arguments')
    base_dir = unicode(args[0])
    if not os.path.exists(os.path.join(base_dir, 'server', 'contest', 'users')):
        raise parser.error('provided path is invalid')

    def get_path(*args):
        return os.path.join(base_dir, 'server', 'contest', *args)

    while not options.name:
        options.name = raw_input('Contest name: ')
    print 'Contest name: ', options.name
    print 'Test environment: ', options.environment

    time_start =  None
    with open(get_path('times', 'start'), 'r') as f:
        time_start = datetime.fromtimestamp(int(f.readline().strip(" \n\t\x00")))
    time_stop =  None
    with open(get_path('times', 'end'), 'r') as f:
        time_stop = datetime.fromtimestamp(int(f.readline().strip(" \n\t\x00")))
    time_freeze =  None
    with open(get_path('times', 'freeze'), 'r') as f:
        time_freeze = datetime.fromtimestamp(int(f.readline().strip(" \n\t\x00")))


    users = {}
    if True:
        for login in os.listdir(get_path('users')):
            with open(get_path('users', login, 'fullname'), 'r') as f:
                fullname = f.readline().strip(" \n\t\x00")
            with open(get_path('users', login, 'password'), 'r') as f:
                password = f.readline().strip(" \n\t\x00")
            users[login] = {
                'login'    : string.lower(login),
                'name'     : fullname,
                'password' : password,
            }

    submits = {}
    if True:
        for d in range(10):
            for submit in os.listdir(get_path('data', str(d))):
                with open(get_path('problem', str(d), submit), 'r') as f:
                    problem = f.readline().strip(" \n\t\x00")
                if problem[0:2] == "__":
                    continue
                with open(get_path('data', str(d), submit), 'r') as f:
                    data = f.read()
                with open(get_path('filename', str(d), submit), 'r') as f:
                    filename = f.readline().strip(" \n\t\x00")
                with open(get_path('time', str(d), submit), 'r') as f:
                    time = datetime.fromtimestamp(int(f.readline().strip(" \n\t\x00")))
                with open(get_path('user', str(d), submit), 'r') as f:
                    user = f.readline().strip().strip(" \n\t\x00")
                with open(get_path('log', str(d), submit), 'r') as f:
                    test_result = {}
                    for tr in [ x.strip(" \n\t\x00[]") for x in re.split(u'\][^[]*\[', u' '.join(f.readlines())) ]:
                        m = re.match(u'^(\d+)\s*:\s*(.+?)\s+(\d+)$', tr)
                        if m:
                            test_result[int(m.group(1))] = {
                                'status' : m.group(2),
                                'time' : int(m.group(3)),
                            }
                            continue
                        m = re.match(u'^(\d+)\s*:\s*(.*)$', tr)
                        if m:
                            test_result[int(m.group(1))] = {
                                'status' : m.group(2),
                                'time' : 0,
                            }
                            continue
                        test_result[0] = {
                            'status' : tr,
                            'time' : 0,
                        }
                with open(get_path('status', str(d), submit), 'r') as f:
                    suite_result = f.readline().strip().strip(" \n\t\x00")
                submit = int(submit)
                submits[submit] = {
                    'submit'       : submit,
                    'data'         : data,
                    'filename'     : filename,
                    'problem'      : problem,
                    'time'         : time,
                    'user'         : user,
                    'test_results' : test_result,
                    'suite_result' : suite_result,
                }

    problems = {}
    if True:
        for dir in os.listdir(get_path()):
            if not os.path.isdir(get_path(dir)):
                continue
            if not os.path.exists(get_path(dir, 'testcount')):
                continue
            with open(get_path(dir, 'testcount')) as f:
                testcount = int(f.readline()) + 1
            with open(get_path(dir, 'sizelimit')) as f:
                sizelimit = int(f.readline())
            if os.path.exists(get_path(dir, 'checker')):
                checker = get_path(dir, 'checker')
            else:
                checker = None
            tests = {}
            for t in range(testcount):
                input = get_path(dir, str(t) + '.in')
                if not os.path.exists(input):
                    input = None
                output = get_path(dir, str(t) + '.out')
                if not os.path.exists(output):
                    output = None
                memlimit = get_path(dir, str(t) + '.mem')
                if os.path.exists(memlimit):
                    with open(memlimit, 'r') as f:
                        memlimit = int(f.readline())
                else:
                    memlimit = None
                timelimit = get_path(dir, str(t) + '.tle')
                if os.path.exists(timelimit):
                    with open(timelimit, 'r') as f:
                        timelimit = timedelta(seconds=float(f.readline())*0.01)
                else:
                    timelimit = None
                tests[t] = {
                    'test'      : t,
                    'input'     : input,
                    'output'    : output,
                    'memlimit'  : memlimit,
                    'timelimit' : timelimit,
                }
            problems[dir] = {
                'problem'   : dir,
                'testcount' : testcount,
                'sizelimit' : sizelimit,
                'checker'   : checker,
                'tests'     : tests,
            }

#    print 'users:    ', users
#    print 'problems: ', problems
#    print 'submits:  ', submits

    mytoken = token_container.get_token()

    contest = Creator('Contest', name=options.name)()
    Privilege.grant(contest.contestant_role, contest, 'SUBMIT')
    Privilege.grant(contest.contestant_role, contest, 'VIEW')
    Privilege.grant(contest.contestant_role, contest, 'VIEW_TASKS')

    for login, user in sorted(users.iteritems()):
        firstname = user['name'].split()[0]
        lastname = ' '.join(user['name'].split()[1:])
        user['object'] = Creator('User', login=options.name + '_' + user['login']).fields(firstname=firstname, lastname=lastname)()
        user['object'].set_password(user['password'])
        user['contestant'] = Creator('Contestant', contest=contest, login=user['object'].login).additional(user_list=[user['object']])()
        user['contestant'].set_password(user['password'])

    for name, problem in sorted(problems.iteritems()):
        problem['object'] = Creator('Problem', name=options.name + '_' + problem['problem'])()
        tests = []
        for num, test in sorted(problem['tests'].iteritems()):
            oa = OaMap()
            if problem['checker'] != None:
                oa.set_blob_path('checker', problem['checker'])
            if test['input'] != None:
                oa.set_blob_path('input', test['input'])
            if test['output'] != None:
                oa.set_blob_path('hint', test['output'])
            if test['memlimit'] != None:
                oa.set_str('memory', str(test['memlimit'])+'B')
            if test['timelimit'] != None:
                oa.set_str('time', str(seconds(test['timelimit']))+'s')
            test['object'] = Creator('Test', problem=problem['object'], name=options.name + '_' + problem['problem'] + '_default_' + str(test['test'])).fields(environment=options.environment).additional(data=oa.get_map())()
            tests.append(test['object'])
        params = OaMap()
        params.set_str('reporter_show_tests', 'true')
        problem['testsuite'] = Creator('TestSuite', problem=problem['object'], name=options.name + '_' + problem['problem'] + '_default').fields(reporter='ACMReporter', dispatcher='SerialDispatcher', accumulators='').additional(test_list=tests, params=params.get_map(), test_params=[{}]*len(tests))()
        problem['mapping'] = Creator('ProblemMapping', contest=contest, problem=problem['object']).fields(code=problem['problem'], title=problem['problem'], default_test_suite=problem['testsuite'])()
    params = OaMap()
    params.set_str('time_start', time_start.strftime('%Y-%m-%d %H:%M:%S'))
    params.set_str('time_stop', time_freeze.strftime('%Y-%m-%d %H:%M:%S'))
    ranking = Creator('Ranking', contest=contest, name='Ranking').fields(is_public=True, aggregator='ACMAggregator').additional(params=params.get_map(), problem_test_suites={}, problem_params={})()
    params = OaMap()
    params.set_str('time_start', time_start.strftime('%Y-%m-%d %H:%M:%S'))
    params.set_str('time_stop', (time_stop + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'))
    full_ranking = Creator('Ranking', contest=contest, name='Full Ranking').fields(is_public=False, aggregator='ACMAggregator').additional(params=params.get_map(), problem_test_suites={}, problem_params={})()
    Privilege.grant(contest.contestant_role, full_ranking, 'VIEW', PrivilegeTimes(start_on=time_stop + timedelta(hours=2)))
    marks_ranking = Creator('Ranking', contest=contest, name='Marks').fields(is_public=False, aggregator='MarksAggregator').additional(params=params.get_map(), problem_test_suites={}, problem_params={})()
    params = OaMap()
    params.set_str('time_start', time_start.strftime('%Y-%m-%d %H:%M:%S'))
    params.set_str('show_invisible', '1')
    admin_ranking = Creator('Ranking', contest=contest, name='Admin Ranking').fields(is_public=False, aggregator='ACMAggregator').additional(params=params.get_map(), problem_test_suites={}, problem_params={})()
    for id, submit in sorted(submits.iteritems()):
        user = users[submit['user']]
        test_results = {}
        problem = problems[submit['problem']]
        for num, test in problem['tests'].iteritems():
            if num in submit['test_results']:
                oa = OaMap()
                oa.set_str('status', unicode(submit['test_results'][num]['status']))
                oa.set_str('execute_time_cpu', unicode(submit['test_results'][num]['time']))
                test_results[test['object']] = oa.get_map()
        submit['object'] = Creator('Submit', contestant=user['contestant'], time=submit['time'], problem=problems[submit['problem']]['mapping']).additional(filename=submit['filename'], content=submit['data'], test_results=test_results).function('inject')()

def athina_import_testsuite():
    from satori.tools import options, setup
    (options, args) = setup()
    if len(args) != 2:
        parser.error('incorrect number of arguments')
    problem = Problem.filter(ProblemStruct(name=unicode(args[0])))[0]
    base_dir = unicode(args[1])
    if not os.path.exists(os.path.join(base_dir, 'testcount')):
    	raise Exception('provided path is invalid')

    def get_path(*args):
        return os.path.join(base_dir, *args)

    with open(get_path('testcount')) as f:
        testcount = int(f.readline()) + 1
    with open(get_path('sizelimit')) as f:
        sizelimit = int(f.readline())
    if os.path.exists(get_path('checker')):
        checker = get_path('checker')
    else:
        checker = None
    judge = get_path('judge')
    if not os.path.exists(judge):
    	raise Exception('judge missing')
    tests = [] 
    for t in range(testcount):
        input = get_path(str(t) + '.in')
        if not os.path.exists(input):
            input = None
        output = get_path(str(t) + '.out')
        if not os.path.exists(output):
            output = None
        memlimit = get_path(str(t) + '.mem')
        if os.path.exists(memlimit):
            with open(memlimit, 'r') as f:
                memlimit = int(f.readline())
        else:
            memlimit = None
        timelimit = get_path(str(t) + '.tle')
        if os.path.exists(timelimit):
            with open(timelimit, 'r') as f:
                timelimit = timedelta(seconds=float(f.readline())*0.01)
        else:
            timelimit = None

        oa = OaMap()
        oa.set_blob_path('judge', judge)
        if checker != None:
            oa.set_blob_path('checker', checker)
        if input != None:
            oa.set_blob_path('input', input)
        if output != None:
            oa.set_blob_path('hint', output)
        if memlimit != None:
            oa.set_str('memory', str(memlimit)+'B')
        if timelimit != None:
            oa.set_str('time', str(seconds(timelimit))+'s')
        tests.append(Creator('Test', problem=problem, name=problem.name + '_import_' + str(t)).additional(data=oa.get_map())())
    params = OaMap()
    testsuite = Creator('TestSuite', problem=problem, name=problem.name + '_import').fields(reporter='ACMReporter', dispatcher='SerialDispatcher', accumulators='').additional(test_list=tests, params=params.get_map(), test_params=[{}]*len(tests))()
