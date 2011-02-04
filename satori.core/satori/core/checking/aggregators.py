# vim:ts=4:sts=4:sw=4:expandtab
import logging
from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta
from blist import blist, sortedset, sortedlist
from operator import attrgetter

from django.db.models import F

from satori.ars import perf
from satori.core.models import Contestant, Test, TestResult, TestSuiteResult, Ranking, RankingEntry, Contest, ProblemMapping, RankingParams
from satori.events import Event, Client2

maxint = 2**31 - 1
max_seconds_per_problem = maxint / 10

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
#        print contestant.id, sort, individual, _row
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

class RestTable2(object):
    def __init__(self, *cols):
        self.col_width = [col[0] for col in cols]
        self.col_name = [col[1] for col in cols]
        self.row_separator = '+' + '+'.join(['-' * width for width in self.col_width]) + '+\n'
        self.header_separator = '+' + '+'.join(['=' * width for width in self.col_width]) + '+\n'
        self.header_row = self.generate_row(*self.col_name)

    def generate_row(self, *items):
        if len(items) != len(self.col_width):
            raise RuntimeError('Item count not equal to column count.')

        max_count = 0
        row_items = []

        for i in range(len(items)):
            item = unicode(items[i])
            width = self.col_width[i]
            row_item = []
            first = 0
            while first < len(item):
                pos = item.rfind(' ', first, first + width)
                if first + width >= len(item):
                    item_elem = item[first:]
                    first = len(item)
                elif pos == -1:
                    item_elem = item[first : first+width]
                    first += width
                else:
                    item_elem = item[first : pos]
                    first = pos + 1
                item_elem = '|' + item_elem + ' ' * (width - len(item_elem))
                row_item.append(item_elem)
            row_items.append(row_item)
            if max_count < len(row_item):
                max_count = len(row_item)

        for i in range(len(items)):
            if len(row_items[i]) < max_count:
                filling = '|' + ' ' * self.col_width[i]
                while len(row_items[i]) < max_count:
                    row_items[i].append(filling)

        return ''.join([''.join([row_items[j][i] for j in range(len(items))]) + '|\n' for i in range(max_count)])


class AggregatorBase(object):
    def __init__(self, supervisor, ranking):
        super(AggregatorBase, self).__init__()
        self.supervisor = supervisor
        self.ranking = ranking
#        self.rest = ReSTTable(ranking)

    def init(self):
        pass
#        self.rest.clear()
    
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

class AggregatorBase2(AggregatorBase):
    def __init__(self, supervisor, ranking):
        super(AggregatorBase2, self).__init__(supervisor, ranking)

        self.test_suites = {}
        self.problems = {}
        self.submit_cache = {}
        self.scores = {}

    def init(self):
        super(AggregatorBase2, self).init()

        self.hide_invisible = (self.ranking.oa_get_str('hide_invisible') or '0') == '1'

        for rp in RankingParams.objects.filter(ranking=self.ranking):
            if rp.test_suite:
                self.test_suites[rp.problem_id] = rp.test_suite

        for p in ProblemMapping.objects.filter(contest__id=self.ranking.contest_id):
            self.problems[p.id] = p
            if p not in self.test_suites:
                self.test_suites[p.id] = p.default_test_suite
                
        self.changed_contestants()

    def changed_contestants(self):
        ranking_entry_cache = dict((r.contestant_id, r) for r in RankingEntry.objects.filter(ranking=self.ranking))

        new_contestants = set()
        old_contestants = set(self.scores.keys())
        for c in Contestant.objects.filter(contest__id=self.ranking.contest_id):
            new_contestants.add(c.id)

            if not c.id in self.scores:
                self.scores[c.id] = self.get_score()

            self.scores[c.id].contestant = c
            self.scores[c.id].hidden = c.invisible and self.hide_invisible
            if c.id in ranking_entry_cache:
                self.scores[c.id].ranking_entry = ranking_entry_cache[c.id]
            else:
                (self.scores[c.id].ranking_entry, created) = RankingEntry.objects.get_or_create(ranking=self.ranking, contestant=c, defaults={'position': maxint})

            self.scores[c.id].update()
    
        for cid in old_contestants:
            if cid not in new_contestants:
                del self.scores[cid]
    
    def created_submits(self, submits):
        for submit in submits:
            self.submit_cache[submit.id] = submit
            self.supervisor.schedule_test_suite_result(self.ranking, submit, self.test_suites[submit.problem_id])
    
    def checked_test_suite_results(self, test_suite_results):
        changed_contestants = set()
        
        for result in test_suite_results:
            s = self.submit_cache[result.submit_id]
            self.scores[s.contestant_id].aggregate(result)
            changed_contestants.add(s.contestant_id)

        for cid in changed_contestants:
            self.scores[cid].update()
    
    def created_contestants(self, contestants):
        pass

class ACMAggregator(AggregatorBase2):
    class ACMScore(object):
        class ACMProblemScore(object):
            def __init__(self, score, problem):
                self.score = score
                self.ok = False
                self.star_count = 0
                self.ok_time = timedelta()
                self.result_list = sortedlist()
                self.problem = problem

            def aggregate(self, result):
                ok = result.oa_get_str('status') == 'OK'
                if ok:
                    self.ok = True
                self.result_list.add((self.score.aggregator.submit_cache[result.submit_id].time, ok))
                if self.ok:
                    self.star_count = 0
                    for (time, ok) in self.result_list:
                        if ok:
                            if self.score.aggregator.time_start:
                                self.ok_time = time - self.score.aggregator.time_start
                            else:
                                self.ok_time = time - datetime.min
                            break
                        self.star_count += 1

            def get_str(self):
                if self.star_count > 0:
                    if self.star_count < self.score.aggregator.star_collapse:
                        return self.problem.code + '*' * self.star_count
                    else:
                        return self.problem.code + '\\ :sup:`(' + str(self.star_count) + ')`\\'
                else:
                    return self.problem.code

        def __init__(self, aggregator):
            self.aggregator = aggregator
            self.hidden = False
            self.scores = {}

        def update(self):
            score_list = [s for s in self.scores.values() if s.ok]
            if self.hidden or not score_list:
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = maxint
                self.ranking_entry.save()
            else:
                points = len([s for s in score_list])
                if self.aggregator.time_start:
                    time = sum([s.ok_time + self.aggregator.star_penalty * s.star_count for s in score_list], timedelta(0))
                else:
                    time = sum([self.aggregator.star_penalty * s.star_count for s in score_list], timedelta(0))
                time_seconds = (time.microseconds + (time.seconds + time.days * 24 * 3600) * 10**6) / 10**6
                time_str = str(timedelta(seconds=time_seconds))
                problems = ' '.join([s.get_str() for s in sorted([s for s in score_list], key=attrgetter('ok_time'))])

                if time_seconds > max_seconds_per_problem:
                    time_seconds = max_seconds_per_problem
        
                self.ranking_entry.row = self.aggregator.table.generate_row('#####', self.contestant.name, str(points), time_str, problems) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = maxint - (max_seconds_per_problem * points) + time_seconds
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            if submit.problem_id not in self.scores:
                self.scores[submit.problem_id] = self.ACMProblemScore(self, self.aggregator.problems[submit.problem_id])
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(ACMAggregator, self).__init__(supervisor, ranking)
        self.table = RestTable2((5, 'Lp.'), (20, 'Name'), (5, 'Score'), (15, 'Time'), (20, 'Tasks'))

    def init(self):
        super(ACMAggregator, self).init()
        
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = ''
        self.ranking.save()
        
        time_start = self.ranking.oa_get_str('time_start')
        if time_start:
            self.time_start = datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
        else:
            self.time_start = None
        self.star_penalty = timedelta(minutes=int(self.ranking.oa_get_str('star_penalty') or '20'))
        self.star_collapse = int(self.ranking.oa_get_str('star_collapse') or '5')
        
    def get_score(self):
        return self.ACMScore(self)


class CountAggregator(AggregatorBase):

    @key_sortable
    class Score(object):
        def __init__(self, aggregator, name, star_penalty, time_start, time_stop, star_collapse):
            self.aggregator = aggregator
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
        
            submit = self.aggregator.submit_cache[result.submit_id]
            if submit.problem_id not in self.problems:
                self.problems[submit.problem_id] = {
                    's' : sortedset(),
                    'f' : None
                }
            u = self.problems[submit.problem_id]
            time = timedelta(0)
            if self.time_start is not None and submit.time > self.time_start:
                time = submit.time - self.time_start
            r = (submit.time, time, result.oa_get_str('status') == 'OK')
            
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
        self.contestant_cache = {}
        self.submit_cache = {}
        self.tsr_map = {}

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
            s = self.submit_cache[result.submit_id]
            c = self.contestant_cache[s.contestant_id]
            if c.invisible and self.hide_invisible:
                continue
            mc = self.contestant[c.id]
            b = mc.get_key()
            mc += result
            a = mc.get_key()
            if a != b:
                self.rest.set_row(c, a, '', mc.get_row())
        self.rest.store()

    def created_submits(self, submits):

        for submit in submits:
            self.submit_cache[submit.id] = submit
            self.supervisor.schedule_test_suite_result(self.ranking, submit, tsmap[submit.problem_id])

    def created_contestants(self, contestants):
        for c in contestants:
            self.contestant_cache[c.id] = c
            if c.id not in self.contestant:
                self.contestant[c.id] = CountAggregator.Score(aggregator=self, name=c.usernames, star_penalty=self.star_penalty, time_start=self.time_start, time_stop=self.time_stop, star_collapse=self.star_collapse)

class CountAggregator(ACMAggregator):
    pass

class MarksAggregator(AggregatorBase):

    def __init__(self, supervisor, ranking):
        super(MarksAggregator, self).__init__(supervisor, ranking)
    
    def recompute_row(self,c):
        row = [c.usernames.rjust(20)]
        total = 0
        for p in self.marked:
            if p in self.scores[c].keys():
                score = self.scores[c][p][0]
                total = total + score
                ss = str(score).rjust(3)
            else:
                ss = ' \- '
            row.append(ss)
        row.append(str(total).rjust(10))
        self.rest.set_row(c,c.usernames,'',row)

    def init(self):
        r = self.ranking
        self.marked = []
        self.scores = {}
        super(MarksAggregator, self).init()
        header = ['Contestant']
        for rp in ProblemMapping.objects.filter(contest=r.contest):
            self.marked.append(rp)
        self.marked.sort(key=lambda p: p.code)
        for rp in self.marked:
            header.append(rp.code)
        for c in Contestant.objects.filter(contest=r.contest):
            if not c.invisible:
                self.scores[c] = {}
                self.recompute_row(c)
        header.append('Total')
#        row = ['aa','1']
        self.rest.add_header(header)
        self.rest.add_footer(header)
        self.rest.store()

        
    def checked_test_suite_results(self, test_suite_results):
        for tr in test_suite_results:
#            print "Found result."
            submit = tr.submit
            p = submit.problem
            c = submit.contestant
            checked = int(tr.oa_get_str('checked'))
            passed = int(tr.oa_get_str('passed'))
            if checked == 0:
                score = 0
            else:
                score = int(100*passed/checked)
#            print c.usernames + "," + p.code + ": "+str(score)
            if not c.invisible and ((not (p in self.scores[c].keys())) or self.scores[c][p][1]<submit.time):
                self.scores[c][p] = [score,submit.time]
                self.recompute_row(c)
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
        for c in contestants:
            if not c.invisible:
                self.scores[c] = {}
                self.recompute_row(c)



aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item
