# vim:ts=4:sts=4:sw=4:expandtab
import logging
from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta
from blist import blist, sortedset

from django.db.models import F

from satori.core.models import Contestant, Test, TestResult, TestSuiteResult, Ranking, RankingEntry, Contest, ProblemMapping, RankingParams
from satori.events import Event, Client2

def key_sortable(cls):
    def lt(self, other):
        return self.get_key() < other.get_key()
    cls.__lt__ = lt
    def eq(self, other):
        return self.get_key() == other.get_key()
    cls.__eq__ = eq
    def hash(self):
        return self.get_key().__hash__()
    cls.__hash__ = hash
    def le(self, other):
        return self.__lt__(other) or self.__eq__(other)
    cls.__le__ = le
    def ne(self, other):
        return not self.__eq__(other)
    cls.__ne__ = ne
    def gt(self, other):
        return not self.__lt__(other) and not self.__eq__(other)
    cls.__gt__ = gt
    def ge(self, other):
        return not self.__lt__(other)
    cls.__ge__ = ge
    return cls

class ReSTTable(object):
    @key_sortable
    class Row(object):
        def __init__(self, contestant, sort, individual, row):
            self.contestant_id = contestant.id
            self.sort = deepcopy(sort)
            self.individual = str(individual)
            self.row = [ str(r) for r in row ]
        def get_key(self):
            return (self.sort, self.contestant_id)

    def __init__(self, ranking):
        super(ReSTTable,self).__init__()
        self.ranking = ranking
        self.clear()

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

    def t_header(self):
        if self.headers:
            res = ''
            for r in self.headers:
                res += self.re_line()+'\n'+self.re_row(r)+'\n'
            res += self.re_thick_line()+'\n';
            return res
        else:
            return self.re_line()+'\n'
    def t_footer(self):
        if self.footers:
            res = ''
            for r in self.footers:
                res += self.re_row(r)+'\n' + self.re_line() + '\n'
            return res
        else:
            return ''
    def t_row(self, i):
        return self.re_row(self.rows[i].row)+'\n' + self.re_line() + '\n'
    def t_body(self):
        res = ''
        for i in range(len(self.rows)):
            res += self.t_row(i)
        return res
    def t_table(self):
        return self.t_header() + self.t_body() + self.t_footer()

    def proc_row(self, r):
        for i in range(len(r)):
            if i >= len(self.column_width):
                self.column_modified = True
                self.column_width.append(len(r[i]))
            else:
                if len(r[i]) > self.column_width[i]:
                    self.colum_modified = True
                    self.column_width[i] = len(r[i])

    def clear(self):
        self.column_width = []
        self.headers = blist()
        self.footers = blist()

        self.rows = sortedset()
        self.c_map = {}

        self.column_width = []

        self.ranking.header = ''
        self.ranking.footer = ''
        self.ranking.save()
        RankingEntry.objects.filter(ranking=self.ranking).delete()
        self.column_modified = False

    def add_header(self, row):
        self.proc_row(row)
        self.headers.append(row)
        self.ranking.header = self.t_header()
        self.ranking.save()
        if self.column_modified:
            self.store()

    def add_footer(self, row):
        self.proc_row(row)
        self.footers.append(row)
        self.ranking.footer = self.t_footer()
        self.ranking.save()
        if self.column_modified:
            self.store()

    def del_row(self, contestant):
        if contestant.id not in self.c_map:
            return
        if False:
            e = RankingEntry.objects.get(ranking=self.ranking, contestant=contestant)
            pos = e.position;
            e.delete()
            RankingEntry.objects.filter(position__gte=pos).update(position=F('position')-1)
        del self.rows[self.rows.index(self.c_map[contestant.id])]
        del self.c_map[contestant.id]
        if self.column_modified:
            self.store()
    
    def set_row(self, contestant, sort, individual, _row):
        print contestant.id, sort, individual, _row
        if contestant.id in self.c_map:
            self.del_row(contestant)
        row = ReSTTable.Row(contestant, sort, individual, _row)
        self.proc_row(row.row)
        self.rows.add(row)
        self.c_map[row.contestant_id] = row
        if False:
            pos = self.rows.index(row)
            RankingEntry.objects.filter(position__gte=pos).update(position=F('position')+1)
            RankingEntry(
                ranking = self.ranking,
                position = pos,
                contestant = contestant,
                individual = individual,
                row = self.t_row(pos),
            ).save()
            if self.column_modified:
                self.store()

    def store(self):
        self.ranking.header = self.t_header()
        self.ranking.footer = self.t_footer()
        self.ranking.save()
        pos = 0
        for row in self.rows:
            contestant = Contestant.objects.get(id=row.contestant_id)
            try:
                r = RankingEntry.objects.get(ranking = self.ranking, contestant = contestant)
            except RankingEntry.DoesNotExist:
                r = RankingEntry(ranking = self.ranking, contestant = contestant)
            r.position = pos
            r.row = self.t_row(pos)
            r.contestant = Contestant.objects.get(id=row.contestant_id)
            r.individual = row.individual
            r.save()
            pos += 1
        self.column_modified = False

class AggregatorBase(object):
    def __init__(self, supervisor, ranking):
        super(AggregatorBase, self).__init__()
        self.supervisor = supervisor
        self.ranking = ranking
        self.rest = ReSTTable(ranking)

    def init(self):
        self.rest.clear()
    
    def checked_test_suite_results(self, test_suite_results):
        raise NotImplementedError

    def rejudged_test_suite_results(self, test_suite_results):
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

    @key_sortable
    class Score(object):
        def __init__(self, name, star_penalty, time_start, time_stop, star_collapse):
            self.problems_solved = 0
            self.time_used = timedelta(0)
            self.name = name
            self.star_penalty = star_penalty
            self.time_start = time_start
            self.time_stop = time_stop
            self.star_collapse = star_collapse
            self.problems = {}

        def get_key(self):
            return (-self.problems_solved, self.time_used)

        def __iadd__(self, result):
            if self.time_stop is not None:
                if result.submit.time > self.time_stop:
                    return self

            if result.submit.problem.id not in self.problems:
                self.problems[result.submit.problem.id] = {
                    's' : sortedset(),
                    'f' : None
                }
            u = self.problems[result.submit.problem.id]
            time = timedelta(0)
            if self.time_start is not None and result.submit.time > self.time_start:
                time = result.submit.time - self.time_start
            r = (result.submit.time, time, result.oa_get_str('status') == 'OK')
            
            if u['f'] is None:
                b = (0, timedelta(0), 0)
            else:
                b = (1, u['f'][1], u['s'].index(u['f']))
            
            u['s'].add(r)
            i = u['s'].index(r)
            if r[2] and ((u['f'] is None) or i <= b[2]):
                u['f'] = r

            if u['f'] is None:
                a = (0, timedelta(0), 0)
            else:
                a = (1, u['f'][1], u['s'].index(u['f']))

            self.problems_solved += a[0] - b[0]
            self.time_used += a[1] - b[1]
            if self.star_penalty is not None:
                self.time_used += self.star_penalty * (a[2] - b[2])
            return self

        def get_row(self):
            stasks = sortedset()
            for id, u in self.problems.items():
                if u['f'] is not None:
                    stasks.add((u['f'][0], ProblemMapping.objects.get(id=id).code, u['s'].index(u['f'])))
            tasks = []
            for t in stasks:
                task = t[1]
                if self.star_penalty is not None:
                    if t[2] < self.star_collapse:
                        task += '*'*t[2]
                    else:
                        task += '\\ :sup:`('+str(t[2])+')`\\ '
                tasks.append(task)
            tu = self.time_used
            tu = (tu.microseconds + (tu.seconds + tu.days * 24 * 3600) * 10**6) / 10**6
            ret = []
            ret.append(str(self.name))
            ret.append(str(self.problems_solved))
            if self.time_start is not None:
                ret.append(str(timedelta(seconds=int(tu))))
            ret.append(' '.join(tasks))
            return ret

    def __init__(self, supervisor, ranking):
        super(CountAggregator, self).__init__(supervisor, ranking)
        self.contestant = {}

    def init(self):
        super(CountAggregator, self).init()
        self.star_penalty = timedelta(minutes=20)
        self.star_collapse = 5
        self.time_start=None 
        self.time_stop=None
        self.hide_invisible=True
        
        oa = self.ranking.oa_get_map()
        if 'time_start' in oa:
            self.time_start = datetime.strptime(oa['time_start'].value, '%Y-%m-%d %H:%M:%S')
        if 'time_stop' in oa:
            self.time_stop = datetime.strptime(oa['time_stop'].value, '%Y-%m-%d %H:%M:%S')
        if 'hide_invisible' in oa:
            self.hide_invisible = bool(oa['hide_invisible'].value == '1')
        
        header = []
        header.append('Name')
        header.append('Score')
        if self.time_start is not None:
            header.append('Time')
        header.append('Tasks')
        self.rest.add_header(header)
        self.rest.add_footer(header)

    def checked_test_suite_results(self, test_suite_results):
        mod = False
        for result in test_suite_results:
            c = result.submit.contestant
            if c.invisible and self.hide_invisible:
                continue
            if c.id not in self.contestant:
                self.contestant[c.id] = CountAggregator.Score(name=c.usernames, star_penalty=self.star_penalty, time_start=self.time_start, time_stop=self.time_stop, star_collapse=self.star_collapse)
            mc = self.contestant[c.id]
            b = mc.get_key()
            mc += result
            a = mc.get_key()
            if a != b:
                self.rest.set_row(c, a, '', mc.get_row())
        self.rest.store()

    def created_submits(self, submits):
        r = self.ranking
        for submit in submits:
            pm = submit.problem
            try:
                rp = RankingParams.objects.get(ranking = r, problem =  pm)
                ts = rp.test_suite
            except RankingParams.DoesNotExist:
                ts = None
            if ts is None:
                ts = pm.default_test_suite
            self.supervisor.schedule_test_suite_result(r, submit, ts)

    def created_contestants(self, contestants):
        pass



class MarksAggregator(AggregatorBase):

    def __init__(self, supervisor, ranking):
        super(MarksAggregator, self).__init__(supervisor, ranking)
    
    def recompute_row(self,c):
        row = [c.usernames.rjust(20)]
        for p in self.marked:
            row.append(self.scores[c].get(p,'\-'))
        row.append('Total'.rjust(20))
        self.rest.set_row(c,c.usernames,'',row)
        self.rest.store()

    def init(self):
        r = self.ranking
        self.marked = []
        self.scores = {}
        super(MarksAggregator, self).init()
        header = ['Contestant'.rjust(20)]
        for rp in ProblemMapping.objects.filter(contest=r.contest):
            self.marked.append(rp)
            header.append(rp.code)
        for c in Contestant.objects.filter(contest=r.contest):
            if not c.invisible:
                self.scores[c] = {}
                self.recompute_row(c)
        header.append('Total'.rjust(10))
#        row = ['aa','1']
        self.rest.add_header(header)
        self.rest.add_footer(header)

        
    def checked_test_suite_results(self, test_suite_results):
        pass

    def created_submits(self, submits):
        print "Detected submit!!!"

    def created_contestants(self, contestants):
        pass



aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item
