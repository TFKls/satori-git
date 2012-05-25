# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab
import json
import logging
import urllib
import urllib2
import yaml
from blist import blist, sortedset, sortedlist
from collections import deque
from copy import deepcopy
from datetime import date, datetime, timedelta
from operator import attrgetter

from django.db.models import F

from satori.ars import perf
from satori.core.models import Contestant, Test, TestResult, TestSuiteResult, Ranking, RankingEntry, Contest, ProblemMapping, RankingParams, TestMapping
from satori.events import Event, Client2
from satori.core.checking.utils import RestTable
from satori.objects import Namespace
from satori.tools.params import parse_params, total_seconds
from satori.core.settings import SECRET_GOOGLE_SPREADSHEET_SERVICE 

maxint = 2*(10**9)

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
            if p.id not in self.test_suites:
                self.test_suites[p.id] = p.default_test_suite
            if p.id not in self.problem_params:
                self.problem_params[p.id] = parse_params(self.__doc__, 'aggregator', 'problem', {})

    def position(self):
        return u''

    def changed_contestants(self):
        ranking_entry_cache = dict((r.contestant_id, r) for r in RankingEntry.objects.filter(ranking=self.ranking))

        new_contestants = set()
        old_contestants = set(self.scores.keys())
        for c in Contestant.objects.filter(contest__id=self.ranking.contest_id, accepted=True):
            new_contestants.add(c.id)

            if not c.id in self.scores:
                self.scores[c.id] = self.get_score()

            self.scores[c.id].contestant = c
            self.scores[c.id].hidden = c.invisible and not getattr(self.params, 'show_invisible', False)
            if c.id in ranking_entry_cache:
                self.scores[c.id].ranking_entry = ranking_entry_cache.pop(c.id)
            else:
                (self.scores[c.id].ranking_entry, created) = RankingEntry.objects.get_or_create(ranking=self.ranking, contestant=c, defaults={'position': self.position()})

            self.scores[c.id].update()
    
        for cid in old_contestants:
            if cid not in new_contestants:
                del self.scores[cid]

        for cid in ranking_entry_cache:
        	ranking_entry_cache[cid].delete()
    
    def created_submits(self, submits):
        for submit in submits:
            self.submit_cache[submit.id] = submit
            self.supervisor.schedule_test_suite_result(self.ranking, submit, self.test_suites[submit.problem_id])
    
    def checked_test_suite_results(self, test_suite_results):
        changed_contestants = set()
        
        for result in test_suite_results:
            s = self.submit_cache[result.submit_id]
            if s.contestant_id in self.scores:
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
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@              <param type="bool"     name="show_zero"      description="Show contestants with zero score" default="false"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@              <param type="time"     name="time_penalty"   description="Penalty for wrong submit" default="1200s"/>
#@              <param type="int"      name="max_stars"      description="Maximal number of stars" default="4"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@              <param type="float"    name="score"          description="Score" default="1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@      </problem>
#@</aggregator>
    """
    def position(self,  score=0, time=maxint, name=''):
        return (u'%09d%09d%s' % (maxint - score, time, name))[0:50]

    class ACMScore(object):
        class ACMProblemScore(object):
            def __init__(self, score, problem):
                self.score = score
                self.ok = False
                self.star_count = 0
                self.ok_time = timedelta()
                self.ok_submit = None
                self.result_list = sortedlist()
                self.problem = problem
                self.params = self.score.aggregator.problem_params[problem.id]

            def aggregate(self, result):
                time = self.score.aggregator.submit_cache[result.submit_id].time
                ok = result.oa_get_str('status') in ['OK', 'ACC']
                if self.params.time_stop and time > self.params.time_stop:
                    return
                if self.params.ignore:
                    return
                if ok:
                    self.ok = True
                self.result_list.add((time, ok, result.submit_id))
                if self.ok:
                    self.star_count = 0
                    for (time, ok, submit_id) in self.result_list:
                        if ok:
                            if self.params.time_start and time > self.params.time_start:
                                self.ok_time = time - self.params.time_start
                            else:
                                self.ok_time = timedelta()
                            self.ok_submit = submit_id
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
            if self.hidden or (not score_list and not self.aggregator.params.show_zero):
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position()
                self.ranking_entry.save()
            else:
                points = int(sum([s.params.score for s in score_list], 0.0))
                time = sum([s.ok_time + self.aggregator.params.time_penalty * s.star_count for s in score_list], timedelta(0))
                time_seconds = int(total_seconds(time))
                time_str = str(timedelta(seconds=time_seconds))
                problems = ' '.join([s.get_str() for s in sorted([s for s in score_list], key=attrgetter('ok_time'))])

                contestant_name = self.aggregator.table.escape(self.contestant.name)
                self.ranking_entry.row = self.aggregator.table.generate_row('',contestant_name, str(points), time_str, problems) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position(points, time_seconds, self.contestant.name)
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
        for pid, params in self.problem_params.iteritems():
            if params.time_start is None:
                params.time_start = self.params.time_start
            if params.time_stop is None:
                params.time_stop = self.params.time_stop

        self.table = RestTable((4, 'Lp.'), (32, 'Name'), (8, 'Score'), (16, 'Time'), (16, 'Tasks'))
        
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = self.table.header_row + self.table.row_separator
        self.ranking.save()
        
    def get_score(self):
        return self.ACMScore(self)

class ACMBoardAggregator(AggregatorBase):
    """
#@<aggregator name="ACM scoreboard">
#@      <general>
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@              <param type="bool"     name="show_zero"      description="Show contestants with zero score" default="false"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_freeze"    description="Freeze time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time"/>
#@              <param type="time"     name="time_penalty"   description="Penalty for wrong submit" default="1200s"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@              <param type="float"    name="score"          description="Score" default="1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@      </problem>
#@</aggregator>
    """
    def position(self,  score=0, time=maxint, name=''):
        return (u'%09d%09d%s' % (maxint - score, time, name))[0:50]

    class ACMScore(object):
        class ACMProblemScore(object):
            def __init__(self, score, problem):
                self.score = score
                self.ok = False
                self.star_count = 0
                self.ok_time = timedelta()
                self.ok_submit = None
                self.result_list = sortedlist()
                self.problem = problem
                self.params = self.score.aggregator.problem_params[problem.id]

            def aggregate(self, result):
                time = self.score.aggregator.submit_cache[result.submit_id].time
                ok = result.oa_get_str('status') in ['OK', 'ACC']
                if self.params.time_stop and time > self.params.time_stop:
                    return
                if self.params.ignore:
                    return
                if ok:
                    self.ok = True
                self.result_list.add((time, ok, result.submit_id))
                self.star_count = 1
                for (time, ok, submit_id) in self.result_list:
                    if ok:
                        if self.params.time_start and time > self.params.time_start:
                            self.ok_time = time - self.params.time_start
                        else:
                            self.ok_time = timedelta()
                        self.ok_submit = submit_id
                        break
                    self.star_count += 1

            def get_str(self):
                if self.ok:
                    return ':tdpos:`'+str(self.star_count).strip(' ')+' ['+str(self.ok_time.seconds//60)+']`'
                else:
                    return ':tdneg:`'+str(self.star_count).strip(' ')+' ['+str(len(str(self.star_count)))+']`'

        def __init__(self, aggregator):
            self.aggregator = aggregator
            self.hidden = False
            self.scores = {}

        def update(self):
            score_list = [s for s in self.scores.values() if s.ok]
            if self.hidden or (not score_list and not self.aggregator.params.show_zero):
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position()
                self.ranking_entry.save()
            else:
                points = int(sum([s.params.score for s in score_list], 0.0))
                time = sum([s.ok_time + self.aggregator.params.time_penalty * s.star_count for s in score_list], timedelta(0))
                time_seconds = int(total_seconds(time))
                time_str = str(timedelta(seconds=time_seconds))
#                problems = ' '.join([s.get_str() for s in sorted([s for s in score_list], key=attrgetter('ok_time'))])

                contestant_name = self.aggregator.table.escape(self.contestant.name)
                row = ['', 'contestant_name',points,time]
                for problem in self.aggregator.problem_list:
                    if self.scores.has_key(problem.id):
                        row.append(self.scores[problem.id].get_str())
                    else:
                        row.append('\-')
#                row.append(points)

                self.ranking_entry.row = self.aggregator.table.generate_row(*row) + self.aggregator.table.row_separator
                print self.ranking_entry.row
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position(points, time_seconds, self.contestant.name)
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            if submit.problem_id not in self.scores:
                self.scores[submit.problem_id] = self.ACMProblemScore(self, self.aggregator.problem_cache[submit.problem_id])
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(ACMBoardAggregator, self).__init__(supervisor, ranking)

    def init(self):
        super(ACMBoardAggregator, self).init()
        for pid, params in self.problem_params.iteritems():
            if params.time_start is None:
                params.time_start = self.params.time_start
            if params.time_stop is None:
                params.time_stop = self.params.time_stop

        self.problem_list = filter(lambda p : not self.problem_params[p.id].ignore, sorted(self.problem_cache.values(), key=attrgetter('code')))
       
        columns = [(4, 'Lp.'), (32, 'Name'), (4, 'Score'), (8, 'Time'),]

        for problem in self.problem_list:
            columns.append((10, problem.code))

        self.table = RestTable(*columns)
        
        rhead = '.. role:: tdpos\n\n.. role:: tdneg\n\n'
        self.ranking.header = rhead+self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = self.table.header_row + self.table.row_separator
        self.ranking.save()
        
    def get_score(self):
        return self.ACMScore(self)


class PointsAggregator(AggregatorBase):
    """
#@<aggregator name="Points aggregator">
#@      <general>
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@              <param type="bool"     name="auto_score" description="Automatic score calculation" default="true"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@      </problem>
#@</aggregator>
    """
    def position(self,  score=0, name=''):
        return (u'%09d%s' % (maxint - score, name))[0:50]
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
                    if self.score.aggregator.params.auto_score:
                        points = int(100*passed/checked)
                    else:
                        points = int(result.oa_get_str('score'))
                if self.score.aggregator.submit_cache[result.submit_id].time > self.last_time:
                    self.last_time = self.score.aggregator.submit_cache[result.submit_id].time
                    self.points = points

        def __init__(self, aggregator):
            self.aggregator = aggregator
            self.hidden = False
            self.scores = {}
            for problem_id in self.aggregator.problem_cache:
                self.scores[problem_id] = self.PointsProblemScore(self, self.aggregator.problem_cache[problem_id])

        def update(self):
            if (self.hidden and not self.aggregator.params.show_invisible) or not any([s.points is not None for s in self.scores.values()]):
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position()
                self.ranking_entry.save()
            else:
                points = sum([self.scores[p.id].points for p in self.aggregator.problem_list if self.scores[p.id].points is not None], 0)
                
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
                self.ranking_entry.position = self.aggregator.position(points, self.contestant.name)
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(PointsAggregator, self).__init__(supervisor, ranking)

    def init(self):
        super(PointsAggregator, self).init()

        self.problem_list = filter(lambda p : not self.problem_params[p.id].ignore, sorted(self.problem_cache.values(), key=attrgetter('code')))
       
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

class MarksAggregator(AggregatorBase):
    """
#@<aggregator name="Marks aggregator">
#@      <general>
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@              <param type="bool"     name="show_tasklist" description="Show tasklist column" default="false"/>
#@              <param type="float"    name="max_score"      description="Maximum score for each problem" default="1"/>
#@              <param type="float"    name="min_score"      description="Minimum score for each problem" default="-1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Ignore submits after"/>
#@              <param type="int"      name="max_stars"      description="Maximal number of stars" default="4"/>
#@              <param type="text"     name="group_points"   description="Number of points for each problem group"/>
#@              <param type="text"     name="points_mark"    description="Marks for points ranges"/>
#@              <param type="bool"     name="show_marks"     description="Show marks" default="false"/>
#@              <param type="bool"     name="show_max_score" description="Show maximum possible score" default="false"/>
#@              <param type="datetime" name="time_start_descent"       description="Descent start time"/>
#@              <param type="time"     name="time_descent"   description="Descent to zero time"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@              <param type="bool"     name="show"           description="Show column for this problem" default="true"/>
#@              <param type="bool"     name="show_max_score" description="Show maximum possible score"/>
#@              <param type="bool"     name="obligatory"     description="Problem is obligatory" default="false"/>
#@              <param type="float"    name="max_score"      description="Maximum score for problem" default="1"/>
#@              <param type="float"    name="min_score"      description="Minimum score for problem" default="-1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Ignore submits after"/>
#@              <param type="datetime" name="time_start_descent"       description="Descent start time"/>
#@              <param type="time"     name="time_descent"   description="Descent to zero time"/>
#@      </problem>
#@</aggregator>
    """
    def position(self,  name=''):
        return (u'%s' % (name))[0:50]

    class MarksScore(object):
        def __init__(self, aggregator):
            self.aggregator = aggregator
            self.hidden = False
            self.scores = {}

        def timed_score(self, score, time, start_descent, descent):
            if time <= start_descent:
                return score
            dif = total_seconds(time - start_descent)
            des = total_seconds(descent)
            if des <= 0:
                return score
            return (1.0 - dif/des) * score

        def update(self):
            if self.hidden:
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position()
                self.ranking_entry.save()
            else:
                all_ok = True
                points = []
                mpoints = []
                for pid in self.aggregator.sorted_problems:
                    problem = self.aggregator.problem_cache[pid]
                    g_score = self.aggregator.group_score[problem.group]
                    params = self.aggregator.problem_params[pid]
                    maxscore = params.max_score
                    minscore = params.min_score
                    if problem.group in self.aggregator.params.group_points:
                        maxscore *= float(self.aggregator.params.group_points[problem.group]) / g_score
                        minscore *= float(self.aggregator.params.group_points[problem.group]) / g_score
                    score = None
                    mscore = maxscore
                    if params.time_start_descent is not None and params.time_descent is not None:
                        mscore = self.timed_score(mscore, datetime.now(), params.time_start_descent, params.time_descent)
                    if minscore is not None and mscore < minscore:
                        mscore = minscore
                    if pid in self.scores:
                        if self.scores[pid].ok:
                            score = maxscore
                            solve_time = self.aggregator.submit_cache[self.scores[pid].ok_submit].time
                            if params.time_start_descent is not None and params.time_descent is not None:
                                score = self.timed_score(score, solve_time, params.time_start_descent, params.time_descent)
                            if minscore is not None and score < minscore:
                                score = minscore
                        else:
                            if params.obligatory:
                                all_ok = False
                    else:
                        if params.obligatory:
                            all_ok = False
                    if score is not None and score > mscore:
                        mscore = score
                    points.append(score)
                    mpoints.append(mscore)
                problems = ' '.join([s.get_str() for s in sorted([s for s in self.scores.values() if s.ok], key=attrgetter('ok_time'))])
                score = sum([p for p in points if p is not None], 0.0)
                mscore = sum([p for p in mpoints if p is not None], 0.0)
                if not all_ok:
                    mark = 'FAIL'
                else:
                    mark = 'UNK (' + '%.2f'%(score,) + ')'

                for mrk, (lower, upper) in self.aggregator.params.points_mark:
                    if score >= lower and score < upper:
                        mark = mrk

                contestant_name = self.aggregator.table.escape(self.contestant.name)
                
                columns = ['', contestant_name]
                if self.aggregator.params.show_marks:
                    columns += [ str(mark) ]
                column = '%.2f'%(score,)
                if self.aggregator.params.show_max_score:
                    column += ' (%.2f)'%(mscore,)
                columns += [column]
                if self.aggregator.params.show_tasklist:
                    columns += [problems]
                pi=0
                for pid in self.aggregator.sorted_problems:
                    params = self.aggregator.problem_params[pid]
                    if params.show:
                        if points[pi] is None:
                            if params.obligatory:
                                column = 'F'
                            else:
                                column = '\\-'
                            if params.show_max_score:
                                column += ' (%.2f)'%(mpoints[pi])
                            columns += [ column ]
                        else:
                            columns += [ '%.2f'%(points[pi],) ]
                    pi += 1

                self.ranking_entry.row = self.aggregator.table.generate_row(*columns) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.aggregator.position(self.contestant.sort_field)
                self.ranking_entry.save()

        def aggregate(self, result):
            submit = self.aggregator.submit_cache[result.submit_id]
            if submit.problem_id not in self.scores:
                self.scores[submit.problem_id] = ACMAggregator.ACMScore.ACMProblemScore(self, self.aggregator.problem_cache[submit.problem_id])
            self.scores[submit.problem_id].aggregate(result)

    def __init__(self, supervisor, ranking):
        super(MarksAggregator, self).__init__(supervisor, ranking)

    def init(self):
        super(MarksAggregator, self).init()

        try:
            self.params.group_points = {}
            gp = yaml.load(self.params.group_points)
            for g,p in gp.iteritems():
                self.params.group_points[unicode(g)] = float(p)
        except:
            self.params.group_points = {}
        try:
            self.params.points_mark = {}
            pm = yaml.load(self.params.points_mark)
            for p,(l,u) in pm.iteritems():
                self.params.points_mark[float(p)] = (float(l), float(u))
        except:
            self.params.points_mark = {}

        for pid, params in self.problem_params.iteritems():
            if params.time_start is None:
                params.time_start = self.params.time_start
            if params.time_stop is None:
                params.time_stop = self.params.time_stop
            if params.time_start_descent is None:
                params.time_start_descent = self.params.time_start_descent
            if params.time_descent is None:
                params.time_descent = self.params.time_descent
            if params.max_score is None:
                params.max_score = self.params.max_score
            if params.min_score is None:
                params.min_score = self.params.min_score
            if params.show_max_score is None:
                params.show_max_score = self.params.show_max_score

        self.sorted_problems = [p.id for p in sorted(self.problem_cache.values(), key=attrgetter('code')) if not self.problem_params[p.id].ignore]
        columns = [(4, 'Lp.'), (32, 'Name')]
        if self.params.show_marks:
            columns += [(16, 'Mark')]
        columns += [(8, 'Score')]
        if self.params.show_tasklist:
            columns += [(16, 'Tasks')]
        self.group_score = {}
        for pid in self.sorted_problems:
            problem = self.problem_cache[pid]
            if self.problem_params[pid].show:
                columns += [(16, problem.code)]
            self.group_score[problem.group] = self.group_score.get(problem.group, 0) + self.problem_params[pid].max_score

        self.table = RestTable(*columns)
        
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        self.ranking.footer = ''
        self.ranking.save()
        
    def get_score(self):
        return self.MarksScore(self)


class ACMProblemStats(AggregatorBase):
    """
#@<aggregator name="ACM Problem Statistics">
#@      <general>
#@              <param type="text"     name="results"   description="Aggregated results"        default="OK,ANS,RTE,TLE,CME,MEM"/>
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@      </problem>
#@</aggregator>
    """

    def __init__(self, supervisor, ranking):
        super(ACMProblemStats, self).__init__(supervisor, ranking)

    def recalculate(self):
        self.ranking.header = self.table.row_separator + self.table.header_row + self.table.header_separator
        for p in self.problem_list:
            if not self.problem_params[p.id].ignore:
                col = [p.code+' \- '+p.title,unicode(self.submitcount[p])] + [unicode(self.stats[p][r]) for r in self.results]
                self.ranking.header += self.table.generate_row(*col)+self.table.row_separator
        fcol = [' **Total** ',' **'+unicode(self.allsubmits)+'** '] + [(' **'+unicode(self.total[r])+'** ') for r in self.results]
        self.ranking.header += self.table.generate_row(*fcol)+self.table.row_separator            
        self.ranking.save()

    def init(self):
        super(ACMProblemStats, self).init()

        self.problem_list = sorted(self.problem_cache.values(), key=attrgetter('code'))
        self.results = self.params.results.split(',')
        self.stats = {}
        self.submitcount = {}
        self.total = {}
        self.allsubmits = 0
        for r in self.results:
            self.total[r] = 0
        for p in self.problem_list:
            self.submitcount[p] = 0
            self.stats[p] = {}
            for r in self.results:
                self.stats[p][r] = 0
        columns = [ (32,'Problem name'),(10,'Submits') ] + [ (8,r) for r in self.results ]
        self.table = RestTable(*columns)
        self.recalculate()

    def changed_contestants(self):
        self.recalculate()
    
    def checked_test_suite_results(self, test_suite_results):
        for result in test_suite_results:
            s = self.submit_cache[result.submit_id]
            if s.contestant.invisible and not self.params.show_invisible:
                continue
            status = result.oa_get_str('status')
            self.submitcount[s.problem] =  self.submitcount[s.problem]+1
            self.allsubmits = self.allsubmits+1
            if status in self.results:
                self.total[status] = self.total[status]+1
                self.stats[s.problem][status] = self.stats[s.problem][status]+1
        self.recalculate()


class GoogleSpreadsheetAggregator(AggregatorBase):
    """
#@<aggregator name="Google Spreadsheet Aggregator">
#@      <general>
#@              <param type="text"     name="admins"         description="Comma separated list of emails of google spreadsheet editors" />
#@              <param type="bool"     name="show_invisible" description="Show invisible submits" default="false"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="ignore"         description="Ignore problem" default="false"/>
#@      </problem>
#@</aggregator>
    """

    def __init__(self, supervisor, ranking):
        super(GoogleSpreadsheetAggregator, self).__init__(supervisor, ranking)
        self.ok = False


    class encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (date, datetime)):
                return unicode(obj.ctime())
            else:
                return json.JSONEncoder.default(self, obj)

    def call(self, action, params=list()):
        try:
            url = SECRET_GOOGLE_SPREADSHEET_SERVICE
            values = {'action': action, 'ranking': self.ranking.id}
            if action == 'create':
            	values['admins'] = self.params.admins
                values['name'] = 'Satori: ' + self.ranking.contest.name + ': ' + self.ranking.name
            if action == 'contestants' or action == 'add_contestants':
            	values['contestants'] = json.dumps(params, cls=self.encoder)
            if action == 'problems' or action == 'add_problems':
            	values['problems'] = json.dumps(params, cls=self.encoder)
            if action == 'tests' or action == 'add_tests':
            	values['tests'] = json.dumps(params, cls=self.encoder)
            if action == 'submits' or action == 'add_submits':
            	values['submits'] = json.dumps(params, cls=self.encoder)
            if action == 'results' or action == 'add_results':
            	values['results'] = json.dumps(params, cls=self.encoder)
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html;q=0.9", "Accept-Charset": "utf8", "Accept-Language": "en-us,en;q=0.5"}

            logging.debug('START: '+urllib.urlencode(values))
            req = urllib2.Request(url, urllib.urlencode(values), headers)
            res = urllib2.urlopen(req).read()
            logging.debug('FINISH: '+urllib.urlencode(values)+': '+res)
        except:
            self.ok = False
            raise

    def recalculate(self):
        self.ok = True
        self.call('create')
        contestants = [ {'id': c.id, 'name': c.name} for c in Contestant.objects.filter(contest__id=self.ranking.contest_id, accepted=True) ]
        self.call('contestants', contestants)
        problems = [ {'id': p.id, 'code': p.code, 'title': p.title, 'group': p.group} for p in self.problem_cache.values() ]
        self.call('problems', problems)
        tests = []
        for pid in self.problem_cache:
        	ts = self.test_suites[pid]
            tests += [ {'id': str(pid)+'_'+str(t.id), 'problem': pid, 'name': t.name} for t in self.test_cache[ts.id] ]
        self.call('tests', tests)
        submits = [ {'id': s.id, 'contestant': s.contestant.id, 'problem': s.problem.id, 'time': s.time} for s in self.submit_cache.values() ]
        self.call('submits', submits)
        self.call('results', self.results)

    def init(self):
        super(GoogleSpreadsheetAggregator, self).init()

        self.contestant_cache = set()
        self.test_cache = {}
        for pid in self.problem_cache:
        	ts = self.test_suites[pid]
            self.test_cache[ts.id] = [tm.test for tm in TestMapping.objects.filter(suite__id=ts.id) ]
        self.results = {}
        self.recalculate()

    def changed_contestants(self):
        if self.ok:
            contestants = [ {'id': c.id, 'name': c.name} for c in Contestant.objects.filter(contest__id=self.ranking.contest_id, accepted=True) ]
            self.call('contestants', contestants)
        else:
        	self.recalculate()
    
    def checked_test_suite_results(self, test_suite_results):
        append = []
        subs = []
        for result in test_suite_results:
            s = self.submit_cache[result.submit_id]
            if s.contestant.invisible and not self.params.show_invisible:
                continue
            pid = s.problem.id
        	ts = self.test_suites[pid]
            for t in self.test_cache[ts.id]:
                try:
                	tr=TestResult.objects.get(submit__id=s.id, test__id=t.id)
                except:
                    continue
            	key = (s.id, pid, t.id)
                if key in self.results:
                	self.ok = False
                val = {'submit': s.id, 'test': str(pid)+'_'+str(t.id)}
                for (k, v) in tr.oa_get_map().iteritems():
                    if not v.is_blob:
                    	val['result_'+k] = v.value
                self.results[key] = val
                append += [val]
        if self.ok:
            self.call('add_results', append)
        else:
        	self.recalculate()

    def created_submits(self, submits):
        if self.ok:
            self.call('add_submits', [ {'id': s.id, 'contestant': s.contestant.id, 'problem': s.problem.id, 'time': s.time} for s in submits ])
        else:
        	self.recalculate()
        logging.debug('hello')
        super(GoogleSpreadsheetAggregator, self).created_submits(submits)


aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item

