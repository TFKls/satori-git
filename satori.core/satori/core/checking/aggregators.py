# vim:ts=4:sts=4:sw=4:expandtab
import logging
from django.db import transaction
from collections import deque
from datetime import datetime, timedelta
from blist import blist, sortedset

from satori.core.checking.utils import wrap_transaction_management
from satori.core.models import Contestant, Test, TestResult, TestSuiteResult, Ranking, RankingEntry, Contest
from satori.events import Event, Client2

class ReSTTable(object):
    def __init__(self, ranking):
        super(ReSTTable,self).__init__()
        self.clear()
        self.ranking = ranking

    def re_line(self):
        return '+'.join([''] + [ '-'*(2+w) for w in self.column_width ] + [''])
    def re_thick_line(self):
        return '+'.join([''] + [ '='*(2+w) for w in self.column_width ] + [''])
    def re_empty(self):
        return '|'.join([''] + [ ' '*(2+w) for w in self.column_width ] + [''])
    def re_fill(self, text, col):
        l = ' '*((self.column_width[col]-len(text)+1)/2+1)
        r = ' '*((self.column_width[col]-len(text))/2+1)
        return l + text + r
    def re_row(self, row):
        filled = []
        for c in range(len(self.column_width)):
            if c < len(row):
                t = row[c]
            else:
                t = ''
            filled.append(self.re_fill(t,c))
        return '|'.join([''] + filled + ['']) + '\n' + self.re_empty()

    def header(self):
        if self.headers:
            res = ''
            for r in self.headers:
                res += self.re_line()+'\n'+self.re_row(r)+'\n'
            res += self.re_thick_line()+'\n';
            return res
        else:
            return self.re_line()+'\n'
    def footer(self):
        if self.footers:
            res = ''
            for r in self.footers:
                res += self.re_row(r)+'\n' + self.re_line() + '\n'
            return res
        else:
            return ''
    def row(self, i):
        return self.re_row(self.rows[i])+'\n' + self.re_line() + '\n'
    def body(self):
        res = ''
        for i in range(len(self.rows)):
            res += self.row(i)
        return res
    def table(self):
        return self.header() + self.body() + self.footer()

    def proc_row(self, r):
        for i in range(len(r)):
            if i >= len(self.column_width):
                self.column_width.append(len(r[i]))
            else:
                if len(r[i]) > self.column_width[i]:
                    self.column_width[i] = len(r[i])
    def clear(self):
        self.column_width = []
        self.headers = blist()
        self.rows = blist()
        self.individual = blist()
        self.contestant_id = blist()
        self.footers = blist()
        self.column_width = []

    def add_header(self, row):
        self.proc_row(row)
        self.headers.append(row)

    def add_footer(self, row):
        self.proc_row(row)
        self.footers.append(row)
    
    def add_row(self, row, individual, contestant):
        self.proc_row(row)
        self.rows.append(row)
        self.individual.append(individual)
        self.contestant_id.append(contestant.id)

    def store(self):
        RankingEntry.objects.filter(ranking=self.ranking).delete()
        self.ranking.header = self.header()
        self.ranking.footer = self.footer()
        self.ranking.save()
        for p,c,i in zip( range(len(self.rows)), self.contestant_id, self.individual):
            RankingEntry(
                ranking = self.ranking,
                position = p,
                row = self.row(p),
                contestant = Contestant.objects.get(id=c),
                individual = i,
            ).save()
        pass


class AggregatorBase(object):
    def __init__(self, supervisor, ranking):
        super(AggregatorBase, self).__init__()
        self.supervisor = supervisor
        self.ranking = ranking

    def init(self):
        self.ranking.header = ''
        self.ranking.footer = ''
        self.ranking.save()
        RankingEntry.objects.filter(ranking=self.ranking).delete()
    
    def checked_test_suite_results(self, test_suite_results):
        raise NotImplementedError

    def rejudge_test_suite_results(self, test_suite_results):
        raise NotImplementedError

    def created_contestants(self, contestants):
        raise NotImplementedError

    def changed_contestant_name(self, contestant):
        raise NotImplementedError

    def hidden_contestant(self, contestant):
        raise NotImplementedError

    def unhidden_contestant(self, contestant):
        raise NotImplementedError

    def tick(self):
        pass

    def changed_default_test_suite(self, problem_mapping):
        raise NotImplementedError

    def created_submits(self, submits):
        raise NotImplementedError

class CountAggregator(AggregatorBase):
    def __init__(self, supervisor, ranking):
        super(CountAggregator, self).__init__(supervisor, ranking)
        self.contestant = {}
        self.rest = ReSTTable(ranking)
        self.rank = sortedset()

    def init(self):
        super(CountAggregator, self).init()

    def checked_test_suite_results(self, test_suite_results):
        mod = False
        for result in test_suite_results:
            if result.oa_get_str('status') == 'OK':
                c = result.submit.contestant
                p = result.submit.problem
                if c.id not in self.contestant:
                    self.contestant[c.id] = {}
                if p.id not in self.contestant[c.id]:
                    mod = True
                    sc = len(self.contestant[c.id])
                    if sc > 0:
                        self.rank.remove((sc, c.id))
                    self.rank.add((sc + 1, c.id))
                    self.contestant[c.id][p.id] = set()
                self.contestant[c.id][p.id].add(result.id)
        if mod:
            self.generate_ranking()

    def created_submits(self, submits):
        r = self.ranking
        for submit in submits:
            pm = submit.problem
            ts = pm.default_test_suite
            self.supervisor.schedule_test_suite_result(r, submit, ts)

    def created_contestants(self, contestants):
        pass

    def generate_ranking(self):
        self.rest.clear()
        self.rest.add_header(['Position', 'Name', 'Score', 'Tasks'])
        self.rest.add_footer(['Position', 'Name', 'Score', 'Tasks'])
        i = 0
        for s, c in reversed(self.rank):
            i += 1
            c = Contestant.objects.get(id=c)
            t = []
            for p in self.contestant[c.id]:
                pm = ProblemMapping.objects.get(id=p)
                t.append(pm.code)
            row = [ str(i), c.name, str(s), ' '.join(t) ]
            self.rest.add_row(row, '', c)
        self.rest.store()


class ICPCAggregator(AggregatorBase):

    class Score(object):
        def __init__(self):
            self.tasks = 0
            self.time = timedelta(0)
        def __init__(self, test_suite_result, task_score = 1, start_time = datetime(2001, 1, 1), time_penalty = timedelta(minutes=20)):
            if test_suite_result.status == 'OK':
                self.tasks = task_score
                count_prev = Submit.objects.filter(contestant = test_suite_result.submit.contestant, problem = test_suite_result.submit.problem, time__lt=test_suite_result.submit.time).count()
                self.time = test_suite_result.submit.time - start_time + time_penalty * count_prev
                if self.time < timedelta(0):
                    self.time = timedelta(0)
            else:
                self.tasks = 0
                self.time = timedelta(0)
        def __eq__(self, other):
            return self.tasks == other.tasks and self.time == other.time
        def __lt__(self, other):
            return self.tasks < other.tasks or self.tasks == other.tasks and self.time > other.time
        def __iadd__(self, other):
            self.tasks += other.tasks
            self.time += other.time
        def __isub__(self, other):
            self.tasks -= other.tasks
            if self.tasks < 0:
                self.tasks = 0
            if self.tasks == 0:
                self.time = timedelta(0)
            self.time -= other.time
            if self.time < timedelta(0):
                self.time = timedelta(0)

    class CScore(object):
        def __init__(self, contestant):
            self.contestant_id = contestant.id
            self.contestant_name = contestant.name
            self.contestant_usernames = contestant.usernames
            self.score = ICPCAggregator.Score()
            self.problems = {}
            self.pscores = {}
        def __eq__(self, other):
            return self.score == other.score
        def __lt__(self, other):
            return self.score < other.score
        def add(self, test_suite_result, task_score = 1, start_time = datetime(2001, 1, 1), time_penalty = timedelta(minutes=20)):
            p = test_suite_result.submit.problem
            if p.id not in self.problems:
                self.problems[p.id] = sortedset()
                self.pscores[p.id] = ICPCAggregator.Score()
            pscore = self.pscores[p.id]
            self.problems[p.id].add(ICPCAggregator.Score(test_suite_result, task_score, start_time, time_penalty))




    def __init__(self, supervisor, ranking):
        super(ICPCAggregator, self).__init__(supervisor, ranking)
        self.contestants = {}
    
    def checked_test_suite_results(self, test_suite_results):
        for result in test_suite_results:
            c = result.submit.contestant
            if c.id not in self.contestants:
                self.contestants[c.id] = ICPCAggregator.CScore()
            self.contestants[c.id].add(result)

    def rejudge_test_suite_results(self, test_suite_results):
        raise NotImplementedError

    def created_contestant(self, contestant):
        raise NotImplementedError

    def changed_contestant_name(self, contestant):
        raise NotImplementedError

    def hidden_contestant(self, contestant):
        raise NotImplementedError

    def unhidden_contestant(self, contestant):
        raise NotImplementedError

    def tick(self):
        pass

    def changed_default_test_suite(self, problem_mapping):
        raise NotImplementedError

    def created_submit(self, submit):
        raise NotImplementedError

aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item
