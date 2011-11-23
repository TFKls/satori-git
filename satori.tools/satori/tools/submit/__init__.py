import logging
import os.path

from satori.client.common import want_import
from satori.tools import config, options, setup, auth_setup, catch_exceptions
want_import(globals(), '*')

@catch_exceptions
def submit():
    options.set_usage('Usage: %prog [options] problem_code submit_file')
    options.add_option('-C', '--contest', type='int', dest='contest', help='contest ID')

    (opts, args) = setup(logging.CRITICAL)

    contestId = None

    if auth_setup.section:
        if config.has_option(auth_setup.section, 'contest'):
            contestId = config.getint(auth_setup.section, 'contest')

    if opts.contest:
    	contestId = options.contest

    if not contestId:
    	raise RuntimeError('The contest ID has not been specified')

    if len(args) != 2:
    	raise RuntimeError('Invalid number of positional parameters specified')

    cc = Contest.filter(ContestStruct(id=contestId))
    if not cc:
    	raise RuntimeError('The specified contest is not found')

    contest = cc[0]

    pp = ProblemMapping.filter(ProblemMappingStruct(contest=contest, code=args[0]))
    if not pp:
    	raise RuntimeError('The specified problem is not found')

    problem = pp[0]

    f = open(args[1], 'r')
    data = f.read()
    f.close()

    submit = Submit.create(SubmitStruct(problem=problem), data, os.path.basename(args[1]))

    print 'Submit successfully created:'
    print '  Contest:', contest.name
    print '  Problem:', problem.code, '-', problem.title
    print '  File:', args[1]
    print '  Submit ID:', submit.id

