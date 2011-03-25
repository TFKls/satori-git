# vim:ts=4:sts=4:sw=4:expandtab

import logging
from satori.core.models import PrivilegeTimes

PageInfo = Struct('PageInfo', [
    ('contest', DjangoStruct('Contest'), False),
    ('contestant', DjangoStruct('Contestant'), False),
    ('role', DjangoStruct('Role'), False),
    ('user', DjangoStruct('User'), False),
    ('subpages', DjangoStructList('Subpage'), False),
    ('rankings', DjangoStructList('Ranking'), False),
    ('is_admin', bool, False),
    ('is_problemsetter', bool, False),
    ('contest_is_admin', bool, False),
    ('contest_can_ask_questions', bool, False),
    ('contest_answers_exist', bool, False),
    ('contest_submittable_problems_exist', bool, False),
    ('contest_viewable_problems_exist', bool, False),
    ])

ContestInfo = Struct('ContestInfo', [
    ('contest', DjangoStruct('Contest'), False),
    ('contestant', DjangoStruct('Contestant'), False),
    ('can_apply', bool, False),
    ('can_join', bool, False),
    ('is_admin', bool, False),
    ])

SizedContestantList = Struct('SizedContestantList', [
    ('contestants', TypedList(DjangoStruct('Contestant')), False),
    ('count', int, False),
    ])

SubpageInfo = Struct('SubpageInfo', [
    ('subpage', DjangoStruct('Subpage'), False),
    ('html', unicode, False),
    ('is_admin', bool, False),
    ])

ProblemMappingInfo = Struct('ProblemMappingInfo', [
    ('problem_mapping', DjangoStruct('ProblemMapping'), False),
    ('can_submit', bool, False),
    ('is_admin', bool, False),
    ('has_pdf', bool, False),
    ('html', unicode, False),
    ('contestant_role_view_times', PrivilegeTimes, False),
    ('contestant_role_submit_times', PrivilegeTimes, False),
    ])

TestResultInfo = Struct('TestResultInfo', [
    ('test', DjangoStruct('Test'), False),
    ('test_result', DjangoStruct('TestResult'), False),
    ('attributes', TypedMap(unicode, AnonymousAttribute), False),
    ])

TestSuiteResultInfo = Struct('TestSuiteResultInfo', [
    ('test_suite', DjangoStruct('TestSuite'), False),
    ('test_suite_result', DjangoStruct('TestSuiteResult'), False),
    ('attributes', TypedMap(unicode, AnonymousAttribute), False),
    ])

ResultInfo = Struct('ResultInfo', [
    ('submit', DjangoStruct('Submit'), False),
    ('contestant', DjangoStruct('Contestant'), False),
    ('problem_mapping', DjangoStruct('ProblemMapping'), False),
    ('status', unicode, False),
    ('report', unicode, False),
    ('data', unicode, False),
    ('data_filename', unicode, False),
    ('test_results', TypedList(TestResultInfo), False),
    ('test_suite_results', TypedList(TestSuiteResultInfo), False),
    ])

SizedResultList = Struct('SizedResultList', [
    ('results', TypedList(ResultInfo), False),
    ('count', int, False),
    ])


@ExportClass
class Web(object):

    @ExportMethod(PageInfo, [DjangoId('Contest')], PCPermit())
    @staticmethod
    def get_page_info(contest=None):
        ret = PageInfo()
        ret.role = Security.whoami()
        ret.user = Security.whoami_user()
        ret.is_admin = Privilege.global_demand('ADMIN')
        ret.is_problemsetter = Privilege.global_demand('MANAGE_PROBLEMS')
        if contest:
            ret.contest = contest
            if ret.role:
                ret.contestant = contest.find_contestant(ret.role)
            else:
                ret.contestant = None
            ret.subpages = Subpage.get_for_contest(contest, False)
            ret.rankings = contest.rankings
            ret.contest_is_admin = Privilege.demand(contest, 'MANAGE')
            ret.contest_can_ask_questions = Privilege.demand(contest, 'ASK_QUESTIONS')
            ret.contest_answers_exist = bool(Privilege.where_can(contest.questions.all(), 'VIEW'))
            ret.contest_submittable_problems_exist = bool(Privilege.where_can(contest.problem_mappings.all(), 'SUBMIT'))
            ret.contest_viewable_problems_exist = bool(Privilege.where_can(contest.problem_mappings.all(), 'VIEW'))
        else:
            ret.subpages = Subpage.get_global(False)
        return ret

    @ExportMethod(TypedList(ContestInfo), [], PCPermit())
    @staticmethod
    def get_contest_list():
        ret = []
        whoami = Security.whoami()
        for contest in Privilege.where_can(Contest.objects.all(), 'VIEW'):
            ret_c = ContestInfo()
            ret_c.contest = contest
            if whoami:
                ret_c.contestant = contest.find_contestant(whoami)
            else:
                ret_c.contestant = None
            ret_c.can_apply = Privilege.demand(contest, 'APPLY')
            ret_c.can_join = Privilege.demand(contest, 'JOIN')
            ret_c.is_admin = Privilege.demand(contest, 'MANAGE')
            ret.append(ret_c)
        return ret

    @ExportMethod(ProblemMappingInfo, [DjangoId('ProblemMapping')], PCPermit())
    @staticmethod
    def get_problem_mapping_info(problem):
        ret_p = ProblemMappingInfo()
        ret_p.problem_mapping = problem
        ret_p.has_pdf = problem.statement_files_get('_pdf') is not None
        reader = problem.statement_files_get_blob('_html')
        if reader:
            ret_p.html = reader.read()
            reader.close()
        ret_p.can_submit = Privilege.demand(problem, 'SUBMIT')
        ret_p.is_admin = Privilege.demand(problem, 'MANAGE')
        if ret_p.is_admin:
            ret_p.contestant_role_view_times = Privilege.get(problem.contest.contestant_role, problem, 'VIEW')
            ret_p.contestant_role_submit_times = Privilege.get(problem.contest.contestant_role, problem, 'SUBMIT')
        return ret_p;

    @ExportMethod(TypedList(ProblemMappingInfo), [DjangoId('Contest')], PCPermit())
    @staticmethod
    def get_problem_mapping_list(contest):
        ret = []
        for problem in Privilege.select_struct_can(Privilege.where_can(contest.problem_mappings.all(), 'VIEW')):
            ret.append(Web.get_problem_mapping_info(problem))
        return ret

    @ExportMethod(SubpageInfo, [DjangoId('Subpage')], PCPermit())
    @staticmethod
    def get_subpage_info(subpage):
        ret_s = SubpageInfo()
        ret_s.subpage = subpage
        reader = subpage.content_files_get_blob('_html')
        if reader:
            ret_s.html = reader.read()
            reader.close()
        ret_s.is_admin = Privilege.demand(subpage, 'MANAGE')
        return ret_s

    @ExportMethod(TypedList(SubpageInfo), [bool], PCPermit())
    @staticmethod
    def get_subpage_list_global(announcements):
        ret = []
        for subpage in Privilege.where_can(Subpage.get_global(announcements), 'VIEW'):
            ret.append(Web.get_subpage_info(subpage))
        return ret

    @ExportMethod(TypedList(SubpageInfo), [DjangoId('Contest'), bool], PCPermit())
    @staticmethod
    def get_subpage_list_for_contest(contest, announcements):
        ret = []
        for subpage in Privilege.where_can(Subpage.get_for_contest(contest, announcements), 'VIEW'):
            ret.append(Web.get_subpage_info(subpage))
        return ret

    @ExportMethod(SizedContestantList, [DjangoId('Contest'), int, int], PCArg('contest', 'VIEW'))
    @staticmethod
    def get_accepted_contestants(contest, limit=20, offset=0):
        result = Privilege.select_struct_can(Contestant.objects.filter(contest=contest, accepted=True).exclude(parents=contest.admin_role))
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])

    @ExportMethod(SizedContestantList, [DjangoId('Contest'), int, int], PCArg('contest', 'MANAGE'))
    @staticmethod
    def get_pending_contestants(contest, limit=20, offset=0):
        result = Privilege.select_struct_can(Contestant.objects.filter(contest=contest, accepted=False).exclude(parents=contest.admin_role))
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])

    @ExportMethod(SizedContestantList, [DjangoId('Contest'), int, int], PCArg('contest', 'MANAGE'))
    @staticmethod
    def get_contest_admins(contest, limit=20, offset=0):
        result = Privilege.select_struct_can(Contestant.objects.filter(parents=contest.admin_role))
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])

    @ExportMethod(SizedResultList, [DjangoId('Contest'), DjangoId('Contestant'), DjangoId('ProblemMapping'), int, int], PCPermit())
    @staticmethod
    def get_results(contest, contestant=None, problem=None, limit=20, offset=0):
        if contestant:
            contestant_list = Contestant.objects.filter(id=contestant.id)
        else:
            contestant_list = Contestant.objects.filter(contest=contest)
        contestant_list = list(Privilege.where_can(contestant_list, 'OBSERVE'))
        q = Submit.objects.filter(contestant__in=contestant_list)
#        if contestant:
#            q = Submit.objects.filter(contestant=contestant)
#        else:
#            q = Submit.objects.filter(contestant__contest=contest)
        if problem:
            q = q.filter(problem=problem)
#        q = Privilege.where_can(q, 'OBSERVE')
        q2 = q.order_by('-id')[offset:offset+limit]
        contestant_dict = {}
#        for c in q2.values_list('contestant', flat=True):
        for c in Privilege.select_struct_can(Contestant.objects.filter(id__in=q2.values_list('contestant', flat=True))):
            contestant_dict[c.id] = c
        problem_dict = {}
        for p in Privilege.select_struct_can(ProblemMapping.objects.filter(id__in=q2.values_list('problem', flat=True))):
            problem_dict[p.id] = p
        ret = []
        for submit in Privilege.select_struct_can(q).order_by('-id')[offset:offset+limit]:
            ret_r = ResultInfo()
            ret_r.submit = submit
            ret_r.contestant = contestant_dict[submit.contestant_id]
            ret_r.problem_mapping = problem_dict[submit.problem_id]
            ret_r.status = submit.get_test_suite_status()
            ret_r.report = submit.get_test_suite_report()
            ret.append(ret_r)
        return SizedResultList(
            count=len(q),
            results=ret
            )
            
    @ExportMethod(ResultInfo, [DjangoId('Submit')], PCArg('submit', 'OBSERVE'))
    @staticmethod
    def get_result_details(submit):
        ret = ResultInfo()
        ret.submit = submit
        ret.contestant = submit.contestant
        ret.problem_mapping = submit.problem
        ret.status = submit.get_test_suite_status()
        ret.report = submit.get_test_suite_report()
        reader = submit.data_get_blob('content')
        data = reader.read(min(100000, reader.length))
        ret.data_filename = reader.filename
        reader.close()
        try:
            ret.data = unicode(data, 'utf8')
        except:
            ret.data = None
        if Privilege.demand(submit, 'MANAGE'):
            ret_tsrs = []
            for tsr in TestSuiteResult.objects.filter(submit=submit):
                ret_tsr = TestSuiteResultInfo()
                ret_tsr.test_suite = tsr.test_suite
                ret_tsr.test_suite_result = tsr
                ret_tsr.attributes = tsr.oa_get_map()
                ret_tsrs.append(ret_tsr)
            ret_trs = []
            for tr in TestResult.objects.filter(submit=submit):
                ret_tr = TestResultInfo()
                ret_tr.test = tr.test
                ret_tr.test_result = tr
                ret_tr.attributes = tr.oa_get_map()
                ret_trs.append(ret_tr)
            ret.test_suite_results = ret_tsrs
            ret.test_results = ret_trs
        return ret

