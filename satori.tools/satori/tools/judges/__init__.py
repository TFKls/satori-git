# vim:ts=4:sts=4:sw=4:expandtab

import logging
import os
import shutil
import sys

from satori.client.common import want_import
want_import(globals(), '*')

def default_judges():
    from satori.tools import options, setup
    options.add_argument('judges_dir')
    args = setup()
    judges_dir = args.judges_dir
    for judge in [ os.path.join(judges_dir, entry) for entry in os.listdir(judges_dir) if os.path.isfile(os.path.join(judges_dir, entry)) ]:
        if judge[-3:] == '.py':
            name = os.path.basename(judge)[:-3]
            blob = Global.get_instance().judges_set_blob_path(name, judge)

def get_judges():
    from satori.tools import options, setup
    options.add_argument('judges_dir')
    options.add_argument('--contest', help='Only for selected contest')
    contest = None
    args = setup()
    judges_dir = args.judges_dir
    if not os.path.exists(judges_dir):
        os.mkdir(judges_dir)
    if args.contest is not None:
        try:
            contest = Contest.filter(ContestStruct(id=int(args.contest)))[0]
        except:
            try:
                contest = Contest.filter(ContestStruct(name=args.contest))[0]
            except:
                pass
    tests = []
    if contest is None:
        tests = [(t, '') for t in Test.filter()]
    else:
        for pm in ProblemMapping.filter(ProblemMappingStruct(contest=contest)):
            tests += [(t, pm.code) for t in pm.default_test_suite.get_tests() ]

    stats = dict()
    for test, code in tests:
        if not code in stats:
            stats[code] = set()
        judge = test.data_get('judge')
        stats[code].add(judge.value)
        ext = judge.filename.split('.')[-1]
        name = os.path.join(judges_dir,judge.value+'.'+ext)
        test.data_get_blob_path('judge', name);
    print stats

def update_judges():
    from satori.tools import options, setup
    options.add_argument('judges_dir')
    options.add_argument('--contest', help='Only for selected contest')
    contest = None
    args = setup()
    judges_dir = args.judges_dir
    if not os.path.exists(judges_dir):
        return
    if args.contest is not None:
        try:
            contest = Contest.filter(ContestStruct(id=int(args.contest)))[0]
        except:
            try:
                contest = Contest.filter(ContestStruct(name=args.contest))[0]
            except:
                pass
    tests = []
    if contest is None:
        tests = [(t, '') for t in Test.filter()]
    else:
        for pm in ProblemMapping.filter(ProblemMappingStruct(contest=contest)):
            tests += [(t, pm.code) for t in pm.default_test_suite.get_tests() ]

    stats = dict()
    for test, code in tests:
        if not code in stats:
            stats[code] = set()
        judge = test.data_get('judge')
        stats[code].add(judge.value)
        fn = judge.filename
        ext = judge.filename.split('.')[-1]
        name = os.path.join(judges_dir,judge.value+'.'+ext)
        if os.path.exists(name):
            oa = OaMap(test.data_get_map())
            oa.set_blob_path('judge', name, filename=fn)
            test.modify_full(TestStruct(), oa.get_map())
    print stats
