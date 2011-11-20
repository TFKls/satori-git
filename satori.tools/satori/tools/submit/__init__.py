import os.path

from satori.client.common import want_import
want_import(globals(), '*')

def submit():
    from satori.tools import config, options, setup, auth_setup

    options.set_usage('Usage: %prog [options] problem_code submit_file')
    options.add_option('-C', '--contest', type='int', dest='contest', help='contest ID')

    (options, args) = setup()

    contestId = None

    if auth_setup.section:
        if config.has_option(auth_setup.section, 'contest'):
            contestId = config.getint(auth_setup.section, 'contest')

    if options.contest:
    	contestId = options.contest

    if not contestId:
    	raise RuntimeError('The contest ID has not been specified')

    if len(args) != 2:
    	raise RuntimeError('Invalid number of positional parameters specified')

    contest = Contest(contestId)

    problem = None

    for p in ProblemMapping.filter(ProblemMappingStruct(contest=contest)):
        if p.code == args[0]:
        	problem = p

    if not problem:
    	raise RuntimeError('The specified problem is not found')

    f = open(args[1], 'r')
    data = f.read()
    f.close()

    submit = Submit.create(SubmitStruct(problem=problem), data, os.path.basename(args[1]))

    print 'Submit successfully created, id={0}'.format(submit.id)

