# vim:ts=4:sts=4:sw=4:expandtab

import os
import shutil
import string
import sys
import traceback

from satori.client.common import want_import
want_import(globals(), '*')

class Creator(object):
    def __init__(self, class_name, **kwargs):
        self._name = class_name
        self._class = globals()[self._name]
        self._struct = globals()[self._name+'Struct']
        self._search = kwargs
        self._create = kwargs
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

    def search(self):
        a = self._class.filter(self._struct(**self._search))
        if len(a):
            return a[0]
        return None
    
    def create(self):
        return self._class.create(self._struct(**self._create), **self._additional)

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
                    time = f.readline().strip(" \n\t\x00")
                with open(get_path('user', str(d), submit), 'r') as f:
                    user = f.readline().strip().strip(" \n\t\x00")
                submit = int(submit)
                submits[submit] = {
                    'submit'   : submit,
                    'data'     : data,
                    'filename' : filename,
                    'problem'  : problem,
                    'time'     : time,
                    'user'     : user,
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
                        timelimit = int(f.readline())
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
        user['object'] = Creator('User', login=options.name + '_' + user['login']).fields(name=user['name'])()
        user['object'].set_password(user['password'])
        user['contestant'] = Creator('Contestant', contest=contest, name=user['object'].login).additional(user_list=[user['object']])()
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
                oa.set_str('memory', str(test['memlimit']))
            if test['timelimit'] != None:
                oa.set_str('time', str(10*int(test['timelimit'])))
            test['object'] = Creator('Test', problem=problem['object'], name=options.name + '_' + problem['problem'] + '_default_' + str(test['test'])).fields(environment=options.environment).additional(data=oa.get_map())()
            tests.append(test['object'])
        problem['testsuite'] = Creator('TestSuite', problem=problem['object'], name=options.name + '_' + problem['problem'] + '_default').fields(reporter='StatusReporter', dispatcher='SerialDispatcher', accumulators='StatusAccumulator').additional(test_list=tests)()
        problem['mapping'] = Creator('ProblemMapping', contest=contest, problem=problem['object']).fields(code=problem['problem'], title=problem['problem'], default_test_suite=problem['testsuite'])()
        Creator('Ranking', contest=contest, name='Ranking').fields(is_public=True, aggregator='CountAggregator')()
        Creator('Ranking', contest=contest, name='Full Ranking').fields(is_public=False, aggregator='CountAggregator')()
    for id, submit in sorted(submits.iteritems()):
        user = users[submit['user']]
        token_container.set_token(User.authenticate(options.name + '_' + user['login'], user['password']))
        Creator('Submit', problem=problems[submit['problem']]['mapping']).additional(filename=submit['filename'], content=submit['data']).create()
    token_container.set_token(mytoken)
