# vim:ts=4:sts=4:sw=4:expandtab
import logging
from blist import sortedlist
from satori.core.checking.utils import RestTable
from satori.core.checking.aggregators import parse_params
from satori.core.models import TestMapping

class ReporterBase(object):
    def __init__(self, test_suite_result):
        super(ReporterBase, self).__init__()
        self.test_suite_result = test_suite_result
        params_map = self.test_suite_result.test_suite.params_get_map()
        new_params_map = {}
        for param_name in params_map:
            if param_name.startswith(self.__class__.__name__ + '.'):
                new_params_map[param_name[len(self.__class__.__name__) + 1:]] = params_map[param_name]
        self.params = parse_params(self.__doc__, 'reporter', 'general', new_params_map)

    def init(self):
        pass

    def accumulate(self, test_result):
        pass

    def status(self):
        return True

    def deinit(self):
        pass

class AssignmentReporter(ReporterBase):
    def __init__(self, test_suite_result):
        super(AssignmentReporter, self).__init__(test_suite_result)

    def init(self):
        self.test_suite_result.oa_set_str('status', 'ACC')
        self.test_suite_result.status = 'ACC'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        pass
        
    def status(self):
        return True

    def deinit(self):
        status = 'ACC'
        report = ''
        oa_map = self.test_suite_result.submit.overrides_get_map()
        ostatus = oa_map.get('status', None)
        if ostatus is not None and not ostatus.is_blob:
            status = ostatus.value
        oreport = oa_map.get('report', None)
        if oreport is not None and not oreport.is_blob:
            report = oreport.value
        self.test_suite_result.status = status
        self.test_suite_result.report = report
        self.test_suite_result.save()
        self.test_suite_result.oa_set_map(oa_map)

class StatusReporter(ReporterBase):
    """
#@<reporter name="Status reporter">
#@      <general>
#@      </general>
#@</reporter>
    """
    def __init__(self, test_suite_result):
        super(StatusReporter, self).__init__(test_suite_result)

    def init(self):
        self._status = 'OK'
        self.test_suite_result.oa_set_str('status', 'QUE')
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        status = test_result.oa_get_str('status')
        logging.debug('Status Reporter %s: %s += %s', self.test_suite_result.id, self._status, status)
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return self._status == 'OK'

    def deinit(self):
        logging.debug('Status Reporter %s: %s', self.test_suite_result.id, self._status)
        status = self._status
        os = self.test_suite_result.submit.overrides_get('status')
        if os is not None and not os.is_blob:
            status = os.value
        self.test_suite_result.oa_set_str('status', status)
        self.test_suite_result.status = status
        self.test_suite_result.report = 'Finished checking: {0}'.format(self._status)
        self.test_suite_result.save()

class MultipleStatusReporter(ReporterBase):
    def __init__(self, test_suite_result):
        super(MultipleStatusReporter, self).__init__(test_suite_result)

    def init(self):
        self._statuses = {}
        self._status = 'OK'
        self.test_suite_result.oa_set_str('status', 'QUE')
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        test = test_result.test
        code = TestMapping.objects.get(test=test, suite=self.test_suite_result.test_suite).order
        status = test_result.oa_get_str('status')
        self._statuses[code] = status
        logging.debug('Status Reporter %s: %s += %s', self.test_suite_result.id, self._status, status)
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return True

    def deinit(self):
        logging.debug('Status Reporter %s: %s', self.test_suite_result.id, self._status)
        status = self._status
        os = self.test_suite_result.submit.overrides_get('status')
        if os is not None and not os.is_blob:
            status = os.value
        self.test_suite_result.oa_set_str('status', status)
        self.test_suite_result.status = status
        report = u'Finished checking: {0}'.format(self._status)
        report += ' (' + u', '.join([unicode(code) + ' ' + unicode(status) for (code, status) in self._statuses.objects().sorted()]) + ')'
        self.test_suite_result.report = report
        self.test_suite_result.save()

class ACMReporter(ReporterBase):
    """
#@<reporter name="ACM style reporter">
#@      <general>
#@              <param type="bool"     name="show_tests"     description="Show individual test results" default="true"/>
#@      </general>
#@</reporter>
    """

    columns = [('status', 'Status'), ('execute_time_cpu', 'CPU time'), ('execute_time_gpu', 'GPU time'), ('message', 'Message')]

    def __init__(self, test_suite_result):
        super(ACMReporter, self).__init__(test_suite_result)

    def init(self):
        self._names = {}
        self._codes = []
        self._column_values = {}
        self._column_nonempty = {}
        self._status = 'OK'
        for (column_id, column_name) in self.columns:
        	self._column_values[column_id] = {}
        	self._column_nonempty[column_id] = False
        self.test_suite_result.oa_set_str('status', 'QUE')
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        test = test_result.test
        code = TestMapping.objects.get(test=test, suite=self.test_suite_result.test_suite).order
        status = test_result.oa_get_str('status')
        for (column_id, column_name) in self.columns:
            value = test_result.oa_get_str(column_id)
            if value is not None:
            	self._column_values[column_id][code] = value
            	self._column_nonempty[column_id] = True
            else:
            	self._column_values[column_id][code] = ''
        self._codes.append(code)
        self._names[code] = test_result.test.name
        logging.debug('ACM Reporter %s: %s += %s', self.test_suite_result.id, self._status, status)
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return self._status == 'OK' or self.params.show_tests

    def deinit(self):
        logging.debug('ACM Reporter %s: %s', self.test_suite_result.id, self._status)
        status = self._status
        os = self.test_suite_result.submit.overrides_get('status')
        if os is not None and not os.is_blob:
            status = os.value
        self.test_suite_result.oa_set_str('status', status)
        self.test_suite_result.status = status
        if self.params.show_tests:
            columns = [(20, 'Test')]
            for (column_id, column_name) in self.columns:
                if self._column_nonempty[column_id]:
                    columns.append((15, column_name))
            table = RestTable(*columns)
            report = table.row_separator + table.header_row + table.header_separator
            for code in sorted(self._codes):
                values = [self._names[code]]
                for (column_id, column_name) in self.columns:
                    if self._column_nonempty[column_id]:
                        values.append(self._column_values[column_id][code])
                report += table.generate_row(*values) + table.row_separator
        else:
            report = ''
        self.test_suite_result.report = report
        self.test_suite_result.save()


class PointsReporter(ReporterBase):
    """
#@<reporter name="Points reporter">
#@      <general>
#@              <param type="bool"     name="show_tests"     description="Show individual test results" default="true"/>
#@              <param type="bool"     name="falling"        description="Linear points decrease" default="false"/>
#@              <param type="bool"     name="show_score"     description="Show score in status" default="false"/>
#@      </general>
#@</reporter>
    """
    def __init__(self, test_suite_result):
        super(PointsReporter, self).__init__(test_suite_result)

    def init(self):
        self.checked = 0
        self.passed = 0
        self.weighted = 0
        self._status = ''
        self.reportlines = sortedlist(key=lambda row: row[0])
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        test = test_result.test
        code = TestMapping.objects.get(test=test, suite=self.test_suite_result.test_suite).order
        result = test_result.oa_get_str('status')
        self.checked = self.checked+1
        if result is None:
            result = 'INT'
        if result == 'OK':
            self.passed = self.passed+1
        self._status = str(self.passed) + ' / '+ str(self.checked)
        if result == 'OK' or result == 'ANS':
            elapsed = test_result.oa_get_str('execute_time_cpu')
        else:
            elapsed = "\-\-"
        limit = test.data_get_str('time')
        if result == 'OK':
            if self.params.falling:
                score = round((2-2*(float(elapsed[:-1])/float(limit[:-1]))),2)
            else:
                score = 1
        else:
            score = 0
        if score<0:
            score = 0
        if score>=1:
            score = 1
        self.weighted += score
        self.normalized = int(100*self.weighted/self.checked)
        line = [test_result.test.name,result,elapsed+' / ' +limit]
        if self.params.falling:
            line.append(unicode(score))
        self.reportlines.add(line)
        self.test_suite_result.save()
        
    def status(self):
        return True

    def deinit(self):
        if self.params.show_tests:
            columns = [(20, 'Test'), (10, 'Status'), (20,'Time')]
            if self.params.falling:
                columns.append((20,'Weighted score'))
            table = RestTable(*columns)
            report = table.row_separator + table.header_row + table.header_separator
            for line in self.reportlines:
                values = line
                report += table.generate_row(*values) + table.row_separator
        else:
            report = ''
        self.test_suite_result.report = report
        if self.params.show_score:
            self.test_suite_result.status = unicode(self.normalized)+' ['+self._status+']'
        else:
            self.test_suite_result.status = self._status            
        self.test_suite_result.oa_set_str('simple_status', self._status)
        self.test_suite_result.oa_set_str('checked', self.checked)
        self.test_suite_result.oa_set_str('passed', self.passed)
        self.test_suite_result.oa_set_str('weighted', self.weighted)
        self.test_suite_result.oa_set_str('score', self.normalized)
        self.test_suite_result.save()


reporters = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, ReporterBase) and (item != ReporterBase):
        reporters[item.__name__] = item
