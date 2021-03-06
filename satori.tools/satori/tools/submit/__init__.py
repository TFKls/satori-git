import argparse
import logging
import os.path

from satori.client.common import want_import
from satori.tools import config, options, setup, auth_setup, catch_exceptions
want_import(globals(), '*')

@catch_exceptions
def submit():
    options.add_argument('-C', '--contest', type=int, help='contest ID')
    options.add_argument('problem_code')
    options.add_argument('submit_file', type=argparse.FileType('r'))

    opts = setup(logging.INFO)

    contestId = None

    if auth_setup.section:
        if config.has_option(auth_setup.section, 'contest'):
            contestId = config.getint(auth_setup.section, 'contest')

    if opts.contest:
    	contestId = options.contest

    if not contestId:
    	raise RuntimeError('The contest ID has not been specified')

    cc = Contest.filter(ContestStruct(id=contestId))
    if not cc:
    	raise RuntimeError('The specified contest is not found')

    contest = cc[0]

    pp = ProblemMapping.filter(ProblemMappingStruct(contest=contest, code=opts.problem_code))
    if not pp:
    	raise RuntimeError('The specified problem is not found')

    problem = pp[0]

    submit = Submit.create(SubmitStruct(problem=problem),
                           opts.submit_file.read(),
                           os.path.basename(opts.submit_file.name))

    opts.submit_file.close()

    print 'Submit successfully created:'
    print '  Contest:', contest.name
    print '  Problem:', problem.code, '-', problem.title
    print '  File:', args[1]
    print '  Submit ID:', submit.id

def rejudge():
    options.add_argument('--submit', type=int, help='submit ID')
    opts = setup(logging.INFO)
    s = Submit.filter(SubmitStruct(id=opts.submit))[0]
    s.rejudge_test_results()
