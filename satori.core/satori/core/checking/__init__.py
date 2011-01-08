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

        self.work_queue = deque()

    def init(self):
        self.attach(self.queue)
        self.map({'type': 'checking_checked_test_result'}, self.queue)
        self.map({'type': 'checking_rejudge_test_result'}, self.queue)
        self.map({'type': 'checking_rejudge_test_suite_result'}, self.queue)
        self.map({'type': 'checking_rejudge_ranking'}, self.queue)
        self.map({'type': 'checking_new_submit'}, self.queue)
        self.map({'type': 'checking_new_contestant'}, self.queue)
        self.map({'type': 'checking_test_result_dequeue'}, self.queue)
        self.map({'type': 'db', 'model': 'core.ranking', 'action': 'I'}, self.queue)

        for test_result in TestResult.objects.filter(pending=True, submit__problem__contest__archived=False):
            self.test_result_queue.append(test_result)
            self.test_result_set.add(test_result)
        for test_suite_result in TestSuiteResult.objects.filter(pending=True, submit__problem__contest__archived=False):
            self.start_test_suite_result(test_suite_result)
        for ranking in Ranking.objects.filter(contest__archived=False):
            self.start_ranking(ranking)

        # do work queue
        self.handle_event(None, Event(type='dummy_event'))

    def handle_event(self, queue, event):
        logging.debug('checking master: event %s', event.type)

        if event.type == 'checking_checked_test_result':
            test_result = TestResult.objects.get(id=event.id)
            self.test_result_judged_set.remove(test_result)
            for test_suite_result in self.scheduled_test_results_map.get(test_result, []):
                self.call_test_suite_result(test_suite_result, 'checked_test_results', [[test_result]])
        elif event.type == 'checking_rejudge_test_result':
            test_result = TestResult.objects.get(id=event.id)
            was_pending = test_result.pending
            if test_result not in self.test_result_set:
                if test_result in self.test_result_judged_set:
                    self.test_result_judged_set.remove(test_result)
                # transaction (?)
                test_result.tester = None
                test_result.pending = True
                test_result.save()
                # end transaction
                self.test_result_queue.append(test_result)
                self.test_result_set.add(test_result)
            if not was_pending:
                for test_suite_result in self.scheduled_test_results_map.get(test_result, []):
                    self.call_test_suite_result(test_suite_result, 'rejudged_test_results', [[test_result]])
            # find finished and start
        elif event.type == 'checking_rejudge_test_suite_result':
            test_suite_result = TestSuiteResult.objects.get(id=event.id)
            was_pending = test_suite_result.pending
            if test_suite_result.submit.problem.contest.archived:
                return
            if test_suite_result in self.test_suite_result_map:
                self.stop_test_suite_result(test_suite_result)
            if was_pending:
                for ranking in self.scheduled_test_suite_results_map.get(test_suite_result, []):
                    self.call_ranking(ranking, 'rejudged_test_suite_results', [[test_suite_result]])
            # transaction (?)
            test_suite_result.pending = True
            test_suite_result.save()
            # end transaction
            self.start_test_suite_result(test_suite_result)
        elif event.type == 'checking_rejudge_ranking':
            ranking = Ranking.objects.get(id=event.id)
            if ranking.contest.archived:
                return
            self.stop_ranking(ranking)
            self.start_ranking(ranking)
        elif event.type == 'checking_new_submit':
            submit = Submit.objects.get(id=event.id)
            if submit.problem.contest.archived:
                return
            self.schedule_test_suite_result(None, submit, submit.problem.default_test_suite)
            for ranking in Ranking.objects.filter(contest=submit.problem.contest, contest__archived=False):
                self.call_ranking(ranking, 'created_submits', [[submit]])
        elif event.type == 'checking_new_contestant':
            contestant = Contestant.objects.get(id=event.id)
            if contetstant.contest.archived:
                return
            for ranking in Ranking.objects.get(contest=contestant.contest):
                self.call_ranking(ranking, 'created_contestants', [[contestant]])
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
        elif event.type == 'db' and event.model == 'core.ranking' and event.action == 'I':
            self.start_ranking(Ranking.objects.get(id=event.object_id))

        while self.work_queue:
            if self.slave.terminated:
                return;

            event = self.work_queue.pop()

            logging.debug('checking master: work item %s', event.type)

            if event.type == 'checked_test_result':
                self.call_test_suite_result(event.test_suite_result, 'checked_test_results', [[event.test_result]])
            elif event.type == 'checked_test_suite_result':
                self.call_ranking(event.ranking, 'checked_test_suite_results', [[event.test_suite_result]])
            elif event.type == 'start_test_suite_result':
                self.start_test_suite_result(event.test_suite_result)

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
            self.work_queue.append(Event(type='checked_test_suite_result', ranking=ranking, test_suite_result=test_suite_result))
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
        if test_result.pending:
            if (test_result not in self.test_result_set) and (test_result not in self.test_result_judged_set):
                logging.debug('Scheduling test result: %s - adding to queue', test_result.id)
                self.test_result_queue.append(test_result)
                self.test_result_set.add(test_result)
            else:
                logging.debug('Scheduling test result: %s - already in queue', test_result.id)
        else:
            logging.debug('Scheduling test result: %s - already checked', test_result.id)
            if test_suite_result is not None:
                self.work_queue.append(Event(type='checked_test_result', test_suite_result=test_suite_result, test_result=test_result))
        if test_suite_result is not None:
            self.scheduled_test_results_map.setdefault(test_result, []).append(test_suite_result)

    # callback
    def schedule_test_suite_result(self, ranking, submit, test_suite):
        (test_suite_result, created) = TestSuiteResult.objects.get_or_create(submit=submit, test_suite=test_suite)
        if test_suite_result.pending:
            if test_suite_result not in self.test_suite_result_map:
                logging.debug('Scheduling test suite result: %s - starting', test_suite_result.id)
                self.work_queue.append(Event(type='start_test_suite_result', test_suite_result=test_suite_result))
            else:
                logging.debug('Scheduling test suite result: %s - already running', test_suite_result.id)
        else:
            logging.debug('Scheduling test suite result: %s - already checked', test_suite_result.id)
            if ranking is not None:
                self.work_queue.append(Event(type='checked_test_suite_result', ranking=ranking, test_suite_result=test_suite_result))
        if ranking is not None:
            self.scheduled_test_suite_results_map.setdefault(test_suite_result, []).append(ranking)

