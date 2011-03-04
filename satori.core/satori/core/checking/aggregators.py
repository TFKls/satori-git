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

maxint = 2*(10**9)

class OaType(object):
    @classmethod
    def name(cls, value):
        raise NotImplemented
    @classmethod
    def value_type(cls):
        raise NotImplemented
    @classmethod
    def cast(cls, value):
        if isinstance(value, cls.value_type()):
            return value
        return cls.value_type()(value)
    @classmethod
    def _from_unicode(cls, value):
        return cls.cast(value)
    @classmethod
    def from_unicode(cls, value):
        return cls.cast(cls._from_unicode(unicode(value)))
    @classmethod
    def _to_unicode(cls, value):
        return unicode(value)
    @classmethod
    def to_unicode(cls, value):
        return unicode(cls._to_unicode(cls.cast(value)))
    def __init__(self, value=None, str_value=None):
        if value is not None:
            self.str_value = self.__class__.to_unicode(value)
        else:
            self.str_value = str_value
    def value(self):
        return self.__class__.from_unicode(self.str_value)

class OaTypeText(OaType):
    @classmethod
    def name(cls):
        return 'text'
    @classmethod
    def value_type(cls):
        return unicode
 
class OaTypeBoolean(OaType):
    @classmethod
    def name(cls):
        return 'bool'
    @classmethod
    def value_type(cls):
        return bool
    @classmethod
    def _to_unicode(cls, value):
        if value:
            return 'true'
        return 'false'
    @classmethod
    def _from_unicode(cls, value):
        value = value.lower()
        if value == 'true' or value == 'yes' or value == '1':
            return True
        elif value == 'false' or value == 'no' or value == '0':
            return False
        raise ValueError
 
class OaTypeInteger(OaType):
    @classmethod
    def name(cls):
        return 'int'
    @classmethod
    def value_type(cls):
        return int
 
class OaTypeFloat(OaType):
    @classmethod
    def name(cls):
        return 'float'
    @classmethod
    def value_type(cls):
        return float
 
class OaTypeTime(OaType):
    scales = [ '', 'd', 'c', 'm', None, None, u'µ', None, None, 'n' ]
    large = [ (60, 'm'), (60*60, 'h'), (24*60*60, 'd'), (7*24*60*60, 'w') ]
    @classmethod
    def name(cls):
        return 'time'
    @classmethod
    def value_type(cls):
        return timedelta
    @classmethod
    def _to_unicode(cls, value):
        large = OaTypeTime.large
        value = float(value.microseconds + (value.seconds + value.days * 24 * 3600) * 10**6) / 10**6
        res = u''
        for mul, suf in reversed(large):
            if value > mul:
                cnt = math.floor(value/mul)
                res += unicode(cnt)+suf
                value -= cnt*mul
        res += unicode(value) + 's'
        return res
    @classmethod
    def _from_unicode(cls, value):
        scales = OaTypeTime.scales
        large = OaTypeTime.large
        value = value.strip().lower()
        parts = []
        for part in value.split():
            found = False
            if not found:
                for s in reversed(range(0, len(scales))):
                    if scales[s] is not None and part.endswith(scales[s] + 's'):
                        parts.append(timedelta(seconds=float(part[:-1*(len(scales[s] + 's'))]) * 0.1**s))
                        found = True
                        break
            if not found:
                for mul, suf in large:
                    if part.endswith(suf):
                        parts.append(timedelta(seconds=float(part[:-1*(len(suf))]) * mul))
                        found = True
                        break
            if not found:
                parts.append(timedelta(seconds=float(value)))
        return sum(parts)
    
class OaTypeSize(OaType):
    scales = [ '', 'K', 'M', 'G', 'T' ]
    @classmethod
    def name(cls):
        return 'size'
    @classmethod
    def value_type(cls):
        return int
    @classmethod
    def _to_unicode(cls, value):
        scales = OaTypeSize.scales
        for s in reversed(range(0, len(scales))):
            if scales[s] is not None and value % (1024**s) == 0:
                return unicode(value / (1024**s)) + scales[s] + 'B'
        return unicode(value)
    @classmethod
    def _from_unicode(cls, value):
        scales = OaTypeSize.scales
        value = value.strip().upper()
        for s in reversed(range(0, len(scales))):
            if scales[s] is not None and value.endswith(scales[s] + 'B'):
                return int(value[:-1*(len(scales[s] + 'B'))]) * 1024**s
        return int(value)

class OaTypeDatetime(OaType):
    @classmethod
    def name(cls):
        return 'datetime'
    @classmethod
    def value_type(cls):
        return datetime
    @classmethod
    def _to_unicode(cls, value):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    @classmethod
    def _from_unicode(cls, value):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

oa_types = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, OaType) and (item != OaType):
        oa_types[item.name()] = item

class OaParam(object):
    def __init__(self, type_, name, description=None, required=False, default=None):
        if not (isinstance(type_, type) and issubclass(type_, OaType)):
            type_ = oa_types[type_]
        self.type_ = type_
        self.name = unicode(name)
        self.description = unicode(description)
        self.required = bool(required)
        if default is None:
            self.default = None
        else:
            self.default = type_.cast(default)
    def to_dom(self, doc):
        ele = doc.createElement('param')
        ele.setAttribute('type', self.type_.name())
        ele.setAttribute('name', self.name)
        if self.description:
            ele.setAttribute('description', self.description)
        if self.required:
            ele.setAttribute('required', 'true')
        if self.default is not None:
            ele.setAttribute('default', self.type_.to_unicode(self.default))
        return ele
    @staticmethod
    def from_dom(ele):
        if ele.tagName != 'param':
            raise ValueError
        type_ = oa_types[ele.getAttribute('type')]
        name = ele.getAttribute('name')
        description = None
        if ele.hasAttribute('description'):
            description = ele.getAttribute('description')
        required = False
        if ele.hasAttribute('required'):
            required = OaTypeBoolean.from_unicode(ele.getAttribute('required'))
        default = None
        if ele.hasAttribute('default'):
            default = type_.from_unicode(ele.getAttribute('default'))
        return OaParam(type_=type_, name=name, description=description, required=required, default=default)
    def to_unicode(self, value):
        return self.type_.to_unicode(value)
    def from_unicode(self, value):
        return self.type_.from_unicode(value)

class OaTypedParser(object):
    def __init__(self, params):
        self.params = params
    @staticmethod
    def from_dom(ele):
        params = []
        for param in ele.getElementsByTagNameNS('*', 'param'):
            params.append(OaParam.from_dom(param))
        return OaTypedParser(params)
    def read_oa_map(self, oa_map):
        result = Namespace()
        for param in self.params:
            value = param.default
            if param.name in oa_map:
                value = param.from_unicode(oa_map[param.name].value)
            if param.required and value is None:
                raise ValueError
            result[param.name] = value
        return result
    def write_oa_map(self, dct):
        result = {}
        for param in self.params:
            if param.name in dct:
                result[param.name] = OpenAttribute(is_blob = False, value = param.to_unicode(dct[param.name]))
        return result

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
    parser = OaTypedParser.from_dom(xml[0])
    return parser.read_oa_map(oa_map)

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
        for c in Contestant.objects.filter(contest__id=self.ranking.contest_id):
            new_contestants.add(c.id)

            if not c.id in self.scores:
                self.scores[c.id] = self.get_score()

            self.scores[c.id].contestant = c
            self.scores[c.id].hidden = c.invisible and not getattr(self.params, 'show_invisible', False)
            if c.id in ranking_entry_cache:
                self.scores[c.id].ranking_entry = ranking_entry_cache[c.id]
            else:
                (self.scores[c.id].ranking_entry, created) = RankingEntry.objects.get_or_create(ranking=self.ranking, contestant=c, defaults={'position': self.position()})

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
#@              <param type="bool"     name="show_invisible" description="Hide invisible submits" required="true" default="false"/>
#@              <param type="bool"     name="show_zero"      description="Hide invisible submits" required="true" default="false"/>
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
    def position(self,  score=0, time=maxint, name=''):
        return (u'%09d%09d%s' % (maxint - score, time, name))[0:50]
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

            def aggregate(self, result):
                time = self.score.aggregator.submit_cache[result.submit_id].time
                ok = result.oa_get_str('status') == 'OK'
                if self.params.time_stop and time > self.params.time_stop:
                    return
                if ok:
                    self.ok = True
                self.result_list.add((time, ok))
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
            if self.hidden or (not score_list and not self.params.show_zero):
                self.ranking_entry.row = ''
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.position()
                self.ranking_entry.save()
            else:
                points = int(sum([s.params.score for s in score_list]))
                time = sum([s.ok_time + self.aggregator.params.time_penalty * s.star_count for s in score_list], timedelta(0))
                time_seconds = (time.microseconds + (time.seconds + time.days * 24 * 3600) * 10**6) / 10**6
                time_str = str(timedelta(seconds=time_seconds))
                problems = ' '.join([s.get_str() for s in sorted([s for s in score_list], key=attrgetter('ok_time'))])

                if time_seconds > max_seconds_per_problem:
                    time_seconds = max_seconds_per_problem
        
                contestant_name = self.aggregator.table.escape(self.contestant.name)

                self.ranking_entry.row = self.aggregator.table.generate_row('', contestant_name, str(points), time_str, problems) + self.aggregator.table.row_separator
                self.ranking_entry.individual = ''
                self.ranking_entry.position = self.position(points, time_seconds, contestant_name)
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
        self.ranking.footer = ''
        self.ranking.save()
        
    def get_score(self):
        return self.ACMScore(self)


class PointsAggregator(AggregatorBase):
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
                self.ranking_entry.position = self.position()
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
                self.ranking_entry.position = self.position(points, contestant_name)
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

class MarksAggregator(AggregatorBase):
    """
#@<aggregator name="Marks aggregator">
#@      <general>
#@              <param type="bool"     name="show_invisible" description="Hide invisible submits" required="true" default="false"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@              <param type="int"      name="max_stars"      description="Maximal number of stars" required="true" default="4"/>
#@              <param type="text"     name="group_points"   description="Number of points for each problem group"/>
#@              <param type="text"     name="points_mark"    description="Marks for points ranges"/>
#@              <param type="datetime" name="time_start_descent"       description="Descent start time"/>
#@              <param type="time"     name="time_descent"   description="Descent to zero time"/>
#@              <param type="bool"     name="below_zero"     description="Score goes below zero" required="true" default="1"/>
#@      </general>
#@      <problem>
#@              <param type="bool"     name="show"           description="Show column for this problem" required="true" default="true"/>
#@              <param type="float"    name="score"          description="Problem Score" required="true" default="1"/>
#@              <param type="bool"     name="obligatory"     description="Problem is obligatory" required="true" default="1"/>
#@              <param type="datetime" name="time_start"     description="Submission start time"/>
#@              <param type="datetime" name="time_stop"      description="Submission stop time (freeze)"/>
#@              <param type="datetime" name="time_start_descent"       description="Descent start time"/>
#@              <param type="time"     name="time_descent"   description="Descent to zero time"/>
#@              <param type="bool"     name="below_zero"     description="Score goes below zero" required="true" default="1"/>
#@      </problem>
#@</aggregator>
    """
    def position(self,  name=''):
        return (u'%s' % (name))[0:50]


aggregators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AggregatorBase) and (item != AggregatorBase):
        aggregators[item.__name__] = item
