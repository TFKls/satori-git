# vim:ts=4:sts=4:sw=4:expandtab

from collections import deque
from django.db import transaction
import logging

from satori.core.models import *
from satori.events import Event, Client2

from dispatchers import dispatchers
from aggregators import aggregators

class CheckingMaster(Client2):
    queue = 'checking_master_queue'

    def __init__(self):
        super(CheckingMaster, self).__init__()

        self.test_result_queue = deque()
        self.test_result_set = set()
        self.test_result_judged_set = set()

        self.test_suite_result_map = dict()
        self.scheduled_test_results_map = dict()

        self.ranking_map = dict()
        self.scheduled_test_suite_results_map = dict()

        self.test_results_to_rejudge = set()
        self.test_suite_result_checked_test_results = dict()
        self.test_suite_result_rejudged_test_results = dict()
        self.test_suite_results_to_start = set()
        self.test_suite_results_to_rejudge = set()
        self.ranking_created_contestants = dict()
        self.ranking_created_submits = dict()
        self.ranking_checked_test_suite_results = dict()
        self.ranking_rejudged_test_suite_results = dict()
        self.rankings_to_rejudge = set()
    
    def init(self):
        self.attach(self.queue)
        self.map({'type': 'checking_rejudge_test'}, self.queue)
        self.map({'type': 'checking_rejudge_test_suite'}, self.queue)
        self.map({'type': 'checking_rejudge_submit'}, self.queue)
        self.map({'type': 'checking_checked_test_result'}, self.queue)
        self.map({'type': 'checking_rejudge_test_result'}, self.queue)
        self.map({'type': 'checking_rejudge_test_suite_result'}, self.queue)
        self.map({'type': 'checking_rejudge_ranking'}, self.queue)
        self.map({'type': 'checking_new_submit'}, self.queue)
        self.map({'type': 'checking_new_contestant'}, self.queue)
        self.map({'type': 'checking_test_result_dequeue'}, self.queue)

        for test_result in TestResult.objects.filter(pending=True, submit__problem__contest__archived=False):
            if test_result.tester:
                test_result.tester = None
                test_result.save()
            self.test_result_queue.append(test_result)
            self.test_result_set.add(test_result)
        for test_suite_result in TestSuiteResult.objects.filter(pending=True, submit__problem__contest__archived=False):
            self.start_test_suite_result(test_suite_result)
        for ranking in Ranking.objects.filter(contest__archived=False):
            self.start_ranking(ranking)

        self.do_work()

    def do_work(self):
        flag = True
        while flag:
            flag = False
            while self.test_suite_results_to_start:
                flag = True
                test_suite_result = self.test_suite_results_to_start.pop()
                self.start_test_suite_result(test_suite_result)
            while self.test_results_to_rejudge:
                flag = True
                test_result = self.test_results_to_rejudge.pop()
                self.do_rejudge_test_result(test_result)
            while self.test_suite_results_to_rejudge:
                flag = True
                test_suite_result = self.test_suite_results_to_rejudge.pop()
                self.do_rejudge_test_suite_result(test_suite_result)
            while self.rankings_to_rejudge:
                flag = True
                ranking = self.rankings_to_rejudge.pop()
                self.do_rejudge_ranking(ranking)
            while self.test_suite_result_rejudged_test_results:
                flag = True
                (test_suite_result, test_results) = self.test_suite_result_rejudged_test_results.popitem()
                self.do_notify_test_suite_result_rejudged_test_results(test_suite_result, test_results)
            while self.test_suite_result_checked_test_results:
                flag = True
                (test_suite_result, test_results) = self.test_suite_result_checked_test_results.popitem()
                self.do_notify_test_suite_result_checked_test_results(test_suite_result, test_results)
            while self.ranking_created_contestants:
                flag = True
                (ranking, contestants) = self.ranking_created_contestants.popitem()
                self.do_notify_ranking_created_contestants(ranking, contestants)
            while self.ranking_created_submits:
                flag = True
                (ranking, submits) = self.ranking_created_submits.popitem()
                self.do_notify_ranking_created_submits(ranking, submits)
            while self.ranking_rejudged_test_suite_results:
                flag = True
                (ranking, test_suite_results) = self.ranking_rejudged_test_suite_results.popitem()
                self.do_notify_ranking_rejudged_test_suite_results(ranking, test_suite_results)
            while self.ranking_checked_test_suite_results:
                flag = True
                (ranking, test_suite_results) = self.ranking_checked_test_suite_results.popitem()
                self.do_notify_ranking_checked_test_suite_results(ranking, test_suite_results)
    
    def do_rejudge_test_result(self, test_result):
        if test_result in self.test_result_set:
            logging.debug('checking master: rejudge test result %s: in queue', test_result.id)
        elif test_result in self.test_result_judged_set:
            logging.debug('checking master: rejudge test result %s: in judge', test_result.id)
            test_result.pending = True
            test_result.tester = None
            test_result.save()
            self.test_result_judged_set.remove(test_result)
            self.test_result_queue.append(test_result)
            self.test_result_set.add(test_result)
        else:
            logging.debug('checking master: rejudge test result %s: rejudge', test_result.id)
            test_result.pending = True
            test_result.tester = None
            test_result.save()
            self.test_result_queue.append(test_result)
            self.test_result_set.add(test_result)
            for test_suite_result in self.scheduled_test_results_map.get(test_result, []):
                self.test_suite_result_rejudged_test_results.setdefault(test_suite_result, set()).add(test_result)
            for test_suite_result in TestSuiteResult.objects.filter(submit=test_result.submit, test_suite__tests=test_result.test):
                if not test_suite_result in self.test_suite_result_map:
                    self.test_suite_results_to_rejudge.add(test_suite_result)

    def do_notify_test_suite_result_rejudged_test_results(self, test_suite_result, rejudged_test_results):
        logging.debug('checking master: notify test suite result %s: rejudged test results %s', test_suite_result.id, ','.join(str(x.id) for x in rejudged_test_results))
        self.call_test_suite_result(test_suite_result, 'rejudged_test_results', [rejudged_test_results])

    def do_notify_test_suite_result_checked_test_results(self, test_suite_result, checked_test_results):
        logging.debug('checking master: notify test suite result %s: checked test results %s', test_suite_result.id, ','.join(str(x.id) for x in checked_test_results))
        self.call_test_suite_result(test_suite_result, 'checked_test_results', [checked_test_results])

    def do_rejudge_test_suite_result(self, test_suite_result):
        if test_suite_result in self.test_suite_result_map:
            logging.debug('checking master: rejudge test suite result %s: running', test_suite_result.id)
            self.stop_test_suite_result(test_suite_result)
            self.start_test_suite_result(test_suite_result)
        else:
            logging.debug('checking master: rejudge test suite result %s: not running', test_suite_result.id)
            test_suite_result = TestSuiteResult.objects.get(id=test_suite_result.id)
            for ranking in self.scheduled_test_suite_results_map.get(test_suite_result, []):
                self.ranking_rejudged_test_suite_results.setdefault(ranking, set()).add(test_suite_result)
            test_suite_result.pending = True
            test_suite_result.save()
            self.start_test_suite_result(test_suite_result)

    def do_notify_ranking_created_submits(self, ranking, created_submits):
        logging.debug('checking master: notify ranking %s: created submits %s', ranking.id, ','.join(str(x.id) for x in created_submits))
        self.call_ranking(ranking, 'created_submits', [created_submits])

    def do_notify_ranking_created_contestants(self, ranking, created_contestants):
        logging.debug('checking master: notify ranking %s: created contestants %s', ranking.id, ','.join(str(x.id) for x in created_contestants))
        self.call_ranking(ranking, 'created_contestants', [created_contestants])

    def do_notify_ranking_rejudged_test_suite_results(self, ranking, rejudged_test_suite_results):
        logging.debug('checking master: notify ranking %s: rejudged test suite results %s', ranking.id, ','.join(str(x.id) for x in rejudged_test_suite_results))
        self.call_ranking(ranking, 'rejudged_test_suite_results', [rejudged_test_suite_results])

    def do_notify_ranking_checked_test_suite_results(self, ranking, checked_test_suite_results):
        logging.debug('checking master: notify ranking %s: checked test suite results %s', ranking.id, ','.join(str(x.id) for x in checked_test_suite_results))
        self.call_ranking(ranking, 'checked_test_suite_results', [checked_test_suite_results])

    def do_rejudge_ranking(self, ranking):
        if ranking in self.ranking_map:
            logging.debug('checking master: rejudge ranking %s: running', ranking.id)
            self.stop_ranking(ranking)
            self.start_ranking(ranking)
        else:
            logging.debug('checking master: rejudge ranking %s: not running', ranking.id)
            self.start_ranking(ranking)

    def handle_event(self, queue, event):
        logging.debug('checking master: event %s', event.type)

        if event.type == 'checking_checked_test_result':
            test_result = TestResult.objects.get(id=event.id)
            if test_result in self.test_result_judged_set:
                logging.debug('checking master: checked test result %s', test_result.id)
                self.test_result_judged_set.remove(test_result)
                for test_suite_result in self.scheduled_test_results_map.get(test_result, []):
                    self.test_suite_result_checked_test_results.setdefault(test_suite_result, set()).add(test_result)
            elif test_result in self.test_result_set:
                logging.error('checking master: checked test in queue')
            else:
                logging.error('checking master: checked test not in queue')
        elif event.type == 'checking_rejudge_test':
            test = Test.objects.get(id=event.id)
            logging.debug('checking master: rejudge test %s', test.id)
            self.test_results_to_rejudge.update(test.test_results.all())
        elif event.type == 'checking_rejudge_test_suite':
            test_suite = TestSuite.objects.get(id=event.id)
            logging.debug('checking master: rejudge test suite %s', test_suite.id)
            self.test_suite_results_to_rejudge.update(test_suite.test_suite_results.all())
        elif event.type == 'checking_rejudge_submit':
            submit = Submit.objects.get(id=event.id)
            logging.debug('checking master: rejudge submit %s', submit.id)
            self.test_results_to_rejudge.update(submit.test_results.all())
            self.test_suite_results_to_rejudge.update(submit.test_suite_results.all())
        elif event.type == 'checking_rejudge_test_result':
            test_result = TestResult.objects.get(id=event.id)
            logging.debug('checking master: rejudge test result %s', test_result.id)
            self.test_results_to_rejudge.add(test_result)
        elif event.type == 'checking_rejudge_test_suite_result':
            test_suite_result = TestSuiteResult.objects.get(id=event.id)
            logging.debug('checking master: rejudge test suite result %s', test_suite_result.id)
            self.test_suite_results_to_rejudge.add(test_suite_result)
        elif event.type == 'checking_rejudge_ranking':
            ranking = Ranking.objects.get(id=event.id)
            logging.debug('checking master: rejudge ranking %s', ranking.id)
            self.rankings_to_rejudge.add(ranking)
        elif event.type == 'checking_new_submit':
            submit = Submit.objects.get(id=event.id)
            logging.debug('checking master: new submit %s', submit.id)
            self.schedule_test_suite_result(None, submit, submit.problem.default_test_suite)
            for ranking in Ranking.objects.filter(contest=submit.problem.contest):
                self.ranking_created_submits.setdefault(ranking, set()).add(submit)
        elif event.type == 'checking_new_contestant':
            contestant = Contestant.objects.get(id=event.id)
            logging.debug('checking master: new contestant %s', contestant.id)
            for ranking in Ranking.objects.filter(contest=contestant.contest):
                self.ranking_created_contestants.setdefault(ranking, set()).add(contestant)
        elif event.type == 'checking_test_result_dequeue':
            e = Event(type='checking_test_result_dequeue_result')
            e.tag = event.tag
            if self.test_result_queue:
                test_result = self.test_result_queue.popleft()
                self.test_result_set.remove(test_result)
                self.test_result_judged_set.add(test_result)
                test_result.tester = Role.objects.get(id=event.tester_id)
                test_result.save()
                e.test_result_id = test_result.id
            else:
                e.test_result_id = None
            logging.debug('Check queue: dequeue by %s: %s', event.tester_id, e)
            self.send(e)

        self.do_work()

    def start_test_suite_result(self, test_suite_result):
        if test_suite_result in self.test_suite_result_map:
            logging.warning('Attempted to start test suite result, but already running: %s', test_suite_result.id)
            return

        logging.debug('Starting test suite result: %s', test_suite_result.id)

        dispatcher = dispatchers[test_suite_result.test_suite.dispatcher]
        self.test_suite_result_map[test_suite_result] = dispatcher(self, test_suite_result)
        self.call_test_suite_result(test_suite_result, 'init', [])

    def call_test_suite_result(self, test_suite_result, name, args):
        if test_suite_result not in self.test_suite_result_map:
            logging.warning('Attempted to call test suite result, but not running: %s.%s', test_suite_result.id, name)
            return

        logging.debug('Calling test suite result: %s.%s', test_suite_result.id, name)

        try:
            transaction.enter_transaction_management(True)
            transaction.managed(True)
            getattr(self.test_suite_result_map[test_suite_result], name)(*args)
        except NotImplementedError:
            transaction.rollback()
            transaction.managed(False)
            transaction.leave_transaction_management()
            self.stop_test_suite_result(test_suite_result)
            self.start_test_suite_result(test_suite_result)
        except:
            logging.exception('Test suite result failed: %s', test_suite_result.id)
            transaction.rollback()
            test_suite_result.status = 'INT'
            test_suite_result.report = 'Internal error'
            test_suite_result.save()
            self.finished_test_suite_result(test_suite_result)
            transaction.commit()
            transaction.managed(False)
            transaction.leave_transaction_management()
        else:
            transaction.commit()
            transaction.managed(False)
            transaction.leave_transaction_management()

    # callback
    def finished_test_suite_result(self, test_suite_result):
        # get fresh version from db
        test_suite_result = TestSuiteResult.objects.get(id=test_suite_result.id)
        test_suite_result.pending = False
        test_suite_result.save()
        for ranking in self.scheduled_test_suite_results_map.get(test_suite_result, []):
            self.ranking_checked_test_suite_results.setdefault(ranking, set()).add(test_suite_result)
        self.stop_test_suite_result(test_suite_result)

    def stop_test_suite_result(self, test_suite_result):
        if test_suite_result not in self.test_suite_result_map:
            logging.warning('Attempted to stop test suite result, but not running: %s', test_suite_result.id)
            return

        logging.debug('Stopping test suite result: %s', test_suite_result.id)

        for (test_result, test_suite_results) in self.scheduled_test_results_map.items():
            if test_suite_result in test_suite_results:
                test_suite_results.remove(test_suite_result)
            if not test_suite_results:
                del self.scheduled_test_results_map[test_result]
        del self.test_suite_result_map[test_suite_result]

    def start_ranking(self, ranking):
        if ranking in self.ranking_map:
            logging.warning('Attempted to start ranking, but already running: %s', ranking.id)
            return

        logging.debug('Starting ranking: %s', ranking.id)

        aggregator = aggregators[ranking.aggregator]
        self.ranking_map[ranking] = aggregator(self, ranking)
        self.call_ranking(ranking, 'init', [])
        self.call_ranking(ranking, 'created_contestants', [Contestant.objects.filter(contest=ranking.contest)])
        self.call_ranking(ranking, 'created_submits', [Submit.objects.filter(problem__contest=ranking.contest)])

    def call_ranking(self, ranking, name, args):
        if ranking not in self.ranking_map:
            logging.warning('Attempted to call ranking, but not running: %s.%s', ranking.id, name)
            return

        logging.debug('Calling ranking: %s.%s', ranking.id, name)

        try:
            transaction.enter_transaction_management(True)
            transaction.managed(True)
            getattr(self.ranking_map[ranking], name)(*args)
        except NotImplementedError:
            transaction.rollback()
            transaction.managed(False)
            transaction.leave_transaction_management()
            self.stop_ranking(ranking)
            self.start_ranking(ranking)
        except:
            logging.exception('Ranking failed: %s', ranking.id)
            transaction.rollback()
            ranking.header = 'Internal error'
            ranking.footer = ''
            ranking.save()
            RankingEntry.objects.filter(ranking=ranking).delete()
            self.stop_ranking(ranking)
            transaction.commit()
            transaction.managed(False)
            transaction.leave_transaction_management()
        else:
            transaction.commit()
            transaction.managed(False)
            transaction.leave_transaction_management()

    def stop_ranking(self, ranking):
        if ranking not in self.ranking_map:
            logging.warning('Attempted to stop ranking, but not running: %s', ranking.id)
            return

        logging.debug('Stopping ranking: %s', ranking.id)

        for (test_suite_result, rankings) in self.scheduled_test_results_map.items():
            if ranking in rankings:
                rankings.remove(ranking)
            if not rankings:
                del self.scheduled_test_results_map[test_suite_result]
        del self.ranking_map[ranking]

    # callback
    def schedule_test_result(self, test_suite_result, submit, test):
        (test_result, created) = TestResult.objects.get_or_create(submit=submit, test=test)
        if (test_result in self.test_result_set) or (test_result in self.test_result_judged_set):
            logging.debug('Scheduling test result: %s - already in queue', test_result.id)
        elif test_result.pending:
            logging.debug('Scheduling test result: %s - adding to queue', test_result.id)
            self.test_result_queue.append(test_result)
            self.test_result_set.add(test_result)
        else:
            logging.debug('Scheduling test result: %s - already checked', test_result.id)
            if test_suite_result is not None:
                self.test_suite_result_checked_test_results.setdefault(test_suite_result, set()).add(test_result)
        if test_suite_result is not None:
            self.scheduled_test_results_map.setdefault(test_result, set()).add(test_suite_result)

    # callback
    def schedule_test_suite_result(self, ranking, submit, test_suite):
        (test_suite_result, created) = TestSuiteResult.objects.get_or_create(submit=submit, test_suite=test_suite)
        if test_suite_result in self.test_suite_result_map:
            logging.debug('Scheduling test suite result: %s - already running', test_suite_result.id)
        elif test_suite_result.pending:
            logging.debug('Scheduling test suite result: %s - starting', test_suite_result.id)
            self.test_suite_results_to_start.add(test_suite_result)
        else:
            logging.debug('Scheduling test suite result: %s - already checked', test_suite_result.id)
            if ranking is not None:
                self.ranking_checked_test_suite_results.setdefault(ranking, set()).add(test_suite_result)
        if ranking is not None:
            self.scheduled_test_suite_results_map.setdefault(test_suite_result, set()).add(ranking)

