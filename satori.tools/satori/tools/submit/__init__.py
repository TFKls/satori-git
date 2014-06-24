from six import print_
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

    print_('Submit successfully created:')
    print_('  Contest:', contest.name)
    print_('  Problem:', problem.code, '-', problem.title)
    print_('  File:', args[1])
    print_('  Submit ID:', submit.id)

