# vim:ts=4:sts=4:sw=4:expandtab

import os
import shutil
import string
import sys
import traceback

from satori.client.common.remote import *

def athina_import():
    import os,sys,getpass
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options] DIR')
    parser.add_option('-U', '--user',
        default='',
        action='store',
        type='string',
        help='Username')
    parser.add_option('-P', '--password',
        default='',
        action='store',
        type='string',
        help='Password')
    parser.add_option('-N', '--name',
        default='',
        action='store',
        type='string',
        help='Contest name')
    parser.add_option('-E', '--environment',
        default='default',
        action='store',
        type='string',
        help='Test environment name')
    (options, args) = parser.parse_args()
    if len(args) != 1:
	    parser.error('incorrect number of arguments')
    base_dir = unicode(args[0])
    if not os.path.exists(os.path.join(base_dir, 'server', 'contest', 'users')):
    	raise parser.error('provided path is invalid')

    def get_path(*args):
        return os.path.join(base_dir, 'server', 'contest', *args)

    if not options.user:
    	options.user = getpass.getuser()
    print 'User: ', options.user
    if not options.password:
        options.password = getpass.getpass('Password: ')
    print 'Password: ', '*' * len(options.password)
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



    mytoken = User.authenticate(options.user, options.password)
    token_container.set_token(mytoken)

    try:
        contest = Contest.create_contest(name=options.name)
    except:
        traceback.print_exc()
        contest = Contest.filter({'name':options.name})[0]
    try:
        Privilege.grant(contest.contestant_role, contest, 'SUBMIT')
        Privilege.grant(contest.contestant_role, contest, 'VIEW')
        Privilege.grant(contest.contestant_role, contest, 'VIEW_TASKS')
    except:
        traceback.print_exc()
        pass

    for login, user in sorted(users.iteritems()):
        try:
            user['object'] = User.register(login=options.name + '_' + user['login'], password=user['password'], name=user['name'])
        except:
            traceback.print_exc()
            pass
        user['object'] = User.filter({'login':options.name + '_' + user['login']})[0]

        try:
            user['contestant'] = contest.create_contestant(name=user['object'].login, user_list=[user['object']])
        except:
            traceback.print_exc()
            user['contestant'] = contest.find_contestant(user['object'])


    for name, problem in sorted(problems.iteritems()):
        try:
        	problem['object'] = Problem.create_problem(name=options.name + '_' + problem['problem'])
        except:
            traceback.print_exc()
            problem['object'] = Problem.filter({'name':options.name + '_' + problem['problem']})[0]

        try:
            problem['testsuite'] = TestSuite.create({'name':options.name + '_' + problem['problem'] + '_default', 'problem':problem['object'], 'dispatcher':'ParallelDispatcher', 'accumulators':'StatusAccumulator'})
            if problem['sizelimit'] != None:
                problem['testsuite'].oa_set_str('sizelimit', str(problem['sizelimit']))
            for num, test in sorted(problem['tests'].iteritems()):
            	test['object'] = Test.create({'name':options.name + '_' + problem['problem'] + '_default_' + str(test['test']), 'problem':problem['object'], 'environment':options.environment})

                if problem['checker'] != None:
                    test['object'].data_set_blob_path('checker', problem['checker'])
                if test['input'] != None:
                    test['object'].data_set_blob_path('input', test['input'])
                if test['output'] != None:
                    test['object'].data_set_blob_path('hint', test['output'])
                if test['memlimit'] != None:
                    test['object'].data_set_str('memory', str(test['memlimit']))
                if test['timelimit'] != None:
                    test['object'].data_set_str('time', str(10*int(test['timelimit'])))
                TestMapping.create({'test':test['object'], 'suite':problem['testsuite'], 'order':test['test']})
        except:
            traceback.print_exc()
            problem['testsuite'] = TestSuite.filter({'name':options.name + '_' + problem['problem'] + '_default'})[0]

        try:
            problem['mapping'] = ProblemMapping.create({'contest':contest, 'problem':problem['object'], 'code':problem['problem'], 'title':problem['problem'], 'default_test_suite':problem['testsuite']})
        except:
            traceback.print_exc()
            problem['mapping'] = ProblemMapping.filter({'contest':contest, 'problem':problem['object']})[0]


    for id, submit in sorted(submits.iteritems()):
    	user = users[submit['user']]
        token_container.set_token(User.authenticate(options.name + '_' + user['login'], user['password']))
    	submit['object'] = contest.submit(filename=submit['filename'], content=submit['data'], problem_mapping=problems[submit['problem']]['mapping'])
    token_container.set_token(mytoken)
