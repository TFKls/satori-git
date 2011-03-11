# vim:ts=4:sts=4:sw=4:expandtab

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
        for problem in Privilege.where_can(contest.problem_mappings.all(), 'VIEW'):
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
        result = Contestant.objects.filter(contest=contest, accepted=True).exclude(parents=contest.admin_role)
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])

    @ExportMethod(SizedContestantList, [DjangoId('Contest'), int, int], PCArg('contest', 'MANAGE'))
    @staticmethod
    def get_pending_contestants(contest, limit=20, offset=0):
        result = Contestant.objects.filter(contest=contest, accepted=False).exclude(parents=contest.admin_role)
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])

    @ExportMethod(SizedContestantList, [DjangoId('Contest'), int, int], PCArg('contest', 'MANAGE'))
    @staticmethod
    def get_contest_admins(contest, limit=20, offset=0):
        result = Contestant.objects.filter(parents=contest.admin_role)
        return SizedContestantList(count=len(result), contestants=result[offset:offset+limit])



