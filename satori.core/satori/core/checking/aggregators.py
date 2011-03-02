# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab
import logging
from blist import blist, sortedset, sortedlist
from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta
from operator import attrgetter
from xml.dom import minidom

from django.db.models import F

from satori.ars import perf
from satori.core.models import Contestant, Test, TestResult, TestSuiteResult, Ranking, RankingEntry, Contest, ProblemMapping, RankingParams
from satori.events import Event, Client2
from satori.core.checking.utils import RestTable
from satori.objects import Namespace

maxint = 2**31 - 1
max_seconds_per_problem = maxint / 10

def parse_params(description, section, subsection, oa_map):
    result = Namespace()
    if not description:
        return result
    xml = minidom.parseString(u' '.join([line[2:] for line in description.splitlines() if line[0:2] == '#@']))
    if not xml:
        return result
    xml = xml.getElementsByTagNameNS('*', section)
    if not xml:
        return result
    xml = xml[0].getElementsByTagNameNS('*', subsection)
    if not xml:
        return result
    xml = xml[0]
    for param in xml.getElementsByTagNameNS('*', 'param'):
        ptype = param.getAttribute('type')
        pname = param.getAttribute('name')
        pdefault = param.getAttribute('default')
        pvalue = pdefault

        oa = oa_map.get(pname)
        if oa is not None and not oa.is_blob:
            pvalue = oa.value

        if pvalue is not None:
            try:
                if ptype == 'int':
                    pvalue = int(pvalue)
                elif ptype == 'size':
                    mul = 1
                    pvalue = unicode(pvalue.strip().lower())
                    if pvalue[-1] == 'b':
                        pvalue = pvalue[:-1]
                    if pvalue[-1] == 'k':
                        mul = 1024
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 'm':
                        mul = 1024**2
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 'g':
                        mul = 1024**3
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 't':
                        mul = 1024**4
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 'p':
                        mul = 1024**5
                        pvalue = pvalue[:-1]
                    pvalue = int(pvalue * mul)
                elif ptype == 'float':
                    pvalue = float(pvalue)
                elif ptype == 'time':
                    pvalue = unicode(pvalue.strip().lower())
                    mul = 1
                    if pvalue[-1] == 's':
                        pvalue = pvalue[:-1]
                    if pvalue[-1] == 'c':
                        mul = 0.01
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 'm':
                        mul = 0.001
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == u'µ':
                        mul = 0.000001
                        pvalue = pvalue[:-1]
                    elif pvalue[-1] == 'n':
                        pvalue = mul = 0.000000001
                        pvalue[0:-1]
                    pvalue = float(pvalue) * mul
                elif ptype == 'datetime':
                    pvalue = datetime.strptime(pvalue, '%Y-%m-%d %H:%M:%S')
                elif ptype == 'bool':
                    if pvalue.lower() == 'true' or pvalue.lower() == 'yes':
                        pvalue = True
                    elif pvalue.lower() == 'false' or pvalue.lower() == 'no':
                        pvalue = False
                    else:
                        pvalue = bool(pvalue)
            except ValueError:
                pass
        result[pname] = pvalue
    return result

class AggregatorBase(object):
    def __init__(self, supervisor, ranking):
        super(AggregatorBase, self).__init__()
        self.supervisor = supervisor
        self.ranking = ranking

        self.test_suites = {}
        self.problem_cache = {}
        self.submit_cache = {}
        self.scores = {}
        self.params = Namespace()
        self.problem_params = {}

    def init(self):
        self.params = parse_params(self.__doc__, 'aggregator', 'general', self.ranking.params_get_map())

        for rp in RankingParams.objects.filter(ranking=self.ranking):
            self.problem_params[rp.problem_id] = parse_params(self.__doc__, 'aggregator', 'problem', rp.params_get_map())
            if rp.test_suite:
                self.test_suites[rp.problem_id] = rp.test_suite

        for p in ProblemMapping.objects.filter(contest__id=self.ranking.contest_id):
            self.problem_cache[p.id] = p
            if p not in self.test_suites:
                self.test_suites[p.id] = p.default_test_suite
                
    def changed_contestants(self):
        ranking_entry_cache = dict((r.contestant_id, r) for r in RankingEntry.objects.filter(ranking=self.ranking))

        new_contestants = set()
        old_contestants = set(self.scores.keys())
        for c in Contestant.objects.filter(contest__id=self.ranking.contest_id):
            new_contestants.add(c.id)

            if not c.id in self.scores:
                self.scores[c.id] = self.get_score()

            self.scores[c.id].contestant = c
            self.scores[c.id].hidden = c.invisible and self.params.hide_invisible
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

    def tick(self):
        pass


class ACMAggregator(AggregatorBase):
    """
#@<aggregator name="ACM style aggregator">
#@      <general>
#@              <param type="bool"     name="hide_invisible" description="Hide invisible submits" required="true" default="true"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@              <param type="time"     name="time_penalty"   description="Penalty for wrong submit" required="true" default="1200s"/>
#@              <param type="int"      name="max_stars"      description="Maximal number of stars" required="true" default="4"/>
#@      </general>
#@      <problem>
#@              <param type="float"    name="score"          description="Score" required="true" default="1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@      </problem>
#@</aggregator>
    """
    class ACMScore(object):
        class ACMProblemScore(object):
            def __init__(self, score, problem):
                self.score = score
                self.ok = False
                self.star_count = 0
                self.ok_time = timedelta()
                self.result_list = sortedlist()
                self.problem = problem
                self.params = self.score.aggregator.problem_params[problem.id]
                print self.params


            def aggregate(self, result):
                time = self.score.aggregator.submit_cache[result.submit_id].time
                ok = result.oa_get_str('status') == 'OK'
                if self.params.time_stop and time > self.params.time_stop:
                    return
                if ok:
                    self.ok = True
                self.result_list.add((time, ok))
                self.result_list.sort()
                if self.ok:
                    self.star_count = 0
                    for (time, ok) in self.result_list:
                        if ok:
                            if self.params.time_start and time > self.params.time_start:
                                self.ok_time = time - self.params.time_start
                            else:
                                self.ok_time = timedelta()
                            break
                        self.star_count += 1

            def get_str(self):
                if self.star_count > 0:
                    if self.star_count <= self.score.aggregator.params.max_stars:
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
                points = int(sum([s.params.score for s in score_list]))
                time = sum([s.ok_time + self.aggregator.time_penalty * s.star_count for s in score_list], timedelta(0))
                time_seconds = (time.microseconds + (time.seconds + time.days * 24 * 3600) * 10**6) / 10**6
                time_str = str(timedelta(seconds=time_seconds))
                problems = ' '.join([s.get_str() for s in sorted([s for s in score_list], key=attrgetter('ok_time'))])

                if time_seconds > max_seconds_per_problem:
                    time_seconds = max_seconds_per_problem
        
                contestant_name = self.aggregator.table.escape(self.contestant.name)

                self.ranking_entry.row = self.aggregator.table.generate_row('', contestant_name, str(points), time_str, problems) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = maxint - (max_seconds_per_problem * points) + time_seconds
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            if submit.problem_id not in self.scores:
                self.scores[submit.problem_id] = self.ACMProblemScore(self, self.aggregator.problem_cache[submit.problem_id])
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(ACMAggregator, self).__init__(supervisor, ranking)

    def init(self):
        super(ACMAggregator, self).init()
        for params in self.problem_params.values():
            if params.time_start is None:
                params.time_start = self.params.time_start
            if params.time_stop is None:
                params.time_stop = self.params.time_stop

        self.table = RestTable((5, 'Lp.'), (20, 'Name'), (5, 'Score'), (15, 'Time'), (20, 'Tasks'))
        
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = ''
        self.ranking.save()
        print self.params
        
    def get_score(self):
        return self.ACMScore(self)


class PointsAggregator(AggregatorBase):
    class PointsScore(object):
        class PointsProblemScore(object):
            def __init__(self, score, problem):
                self.score = score
                self.points = None
                self.last_time = datetime.min
                self.problem = problem

            def aggregate(self, result):
                checked = int(result.oa_get_str('checked'))
                passed = int(result.oa_get_str('passed'))
                if checked == 0:
                    points = 0
                else:
                    points = int(100*passed/checked)
                if self.score.aggregator.submit_cache[result.submit_id].time > self.last_time:
                    self.points = points

        def __init__(self, aggregator):
            self.aggregator = aggregator
            self.hidden = False
            self.scores = {}
            for problem_id in self.aggregator.problem_cache:
                self.scores[problem_id] = self.PointsProblemScore(self, self.aggregator.problem_cache[problem_id])

        def update(self):
            if self.hidden or not any([s.points is not None for s in self.scores.values()]):
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = maxint
                self.ranking_entry.save()
            else:
                points = sum([s.points for s in self.scores.values() if s.points is not None])
                
                contestant_name = self.aggregator.table.escape(self.contestant.name)
        
                row = ['', contestant_name]
                for problem in self.aggregator.problem_list:
                    if self.scores[problem.id].points is not None:
                        row.append(self.scores[problem.id].points)
                    else:
                        row.append('\-')
                row.append(points)

                self.ranking_entry.row = self.aggregator.table.generate_row(*row) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = maxint - points
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(PointsAggregator, self).__init__(supervisor, ranking)

    def init(self):
        super(PointsAggregator, self).init()

        self.problem_list = sorted(self.problem_cache.values(), key=attrgetter('code'))
       
        columns = [(5, 'Lp.'), (20, 'Name')]

        for problem in self.problem_list:
            columns.append((10, problem.code))

        columns.append((10, 'Sum'))

        self.table = RestTable(*columns)
        
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = ''
        self.ranking.save()

    def get_score(self):
        return self.PointsScore(self)


aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item
