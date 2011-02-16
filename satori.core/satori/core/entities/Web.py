# vim:ts=4:sts=4:sw=4:expandtab

PageInfo = Struct('PageInfo', [
    ('contest', DjangoStruct('Contest'), False),
    ('contestant', DjangoStruct('Contestant'), False),
    ('role', DjangoStruct('Role'), False),
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

@ExportClass
class Web(object):

    @ExportMethod(PageInfo, [DjangoId('Contest')], PCPermit())
    def get_general_page_overview(contest=None):
        ret = PageInfo()
        ret.role = Security.whoami()
        ret.is_problemsetter = Privilege.global_demand('ADMIN')
        ret.is_problemsetter = Privilege.global_demand('MANAGE_PROBLEMS')
        if contest:
            ret.contest = contest
            ret.contestant = contest.find_contestant(ret.role)
            ret.subpages = Subpage.get_for_contest(contest, False)
            ret.rankings = contest.rankings
            ret.contest_is_admin = Privilege.demand(contest, 'MANAGE')
            ret.contest_can_ask_questions = Privilege.demand(contest, 'ASK_QUESTIONS')
            ret.contest_answers_exist = bool(Privilege.where_can(contest.questions, 'VIEW'))
            ret.contest_submittable_problems_exist = bool(Privilege.where_can(contest.problems, 'SUBMIT'))
            ret.contest_viewable_problems_exist = bool(Privilege.where_can(contest.problems, 'VIEW'))
        else:
            ret.subpages = Subpage.get_global(False)
        return ret

    @ExportMethod(TypedList(ContestInfo), [], PCPermit())
    def get_contest_list():
        ret = []
        for contest in Privilege.where_can(Contest.objects.all(), 'VIEW'):
            ret_c = ContestInfo()
            ret_c.contest = contest
            ret_c.contestant = contest.find_contestant(Security.whoami())
            ret_c.can_apply = Privilege.demand(contest, 'APPLY')
            ret_c.can_join = Privilege.demand(contest, 'JOIN')
            ret_c.is_admin = Privilege.demand(contest, 'MANAGE')
            ret.append(ret_c)
        return ret

