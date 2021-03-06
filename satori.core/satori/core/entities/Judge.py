# vim:ts=4:sts=4:sw=4:expandtab

"""
Judge helper procedures.
"""

from types import NoneType

from satori.core.dbev   import Events
from satori.core.models import Role
from satori.events      import Event

SubmitToCheck = Struct('SubmitToCheck', (
    ('test_result', long, True),
    ('test_data', TypedMap(unicode, AnonymousAttribute), False),
    ('submit_data', TypedMap(unicode, AnonymousAttribute), False),
))

@ExportClass
class Judge(object):
    """
    """
    @ExportMethod(SubmitToCheck, [], PCGlobal('JUDGE'))
    @staticmethod
    def get_next():
        from satori.core.checking.check_queue_client import check_queue_client
        r = token_container.token.role

        next = check_queue_client.get_next(r)

        if next.test_result_id is None:
            return None

        ret = SubmitToCheck()
        ret.test_result = next.test_result_id

        if next.test_result_id > 0:
            test_result = TestResult.objects.get(id=next.test_result_id)
            ret.test_data = test_result.test.data_get_map()
            ret.submit_data = test_result.submit.data_get_map()
        else:
            temporary_submit = TemporarySubmit.objects.get(id=-next.test_result_id)
            ret.test_data = temporary_submit.test_data_get_map()
            ret.submit_data = temporary_submit.submit_data_get_map()

        return ret

    @ExportMethod(SubmitToCheck, [], PCGlobal('JUDGE'))
    @staticmethod
    def kolejka_get_next():
        from satori.core.checking.check_queue_client import kolejka_check_queue_client
        r = token_container.token.role

        next = kolejka_check_queue_client.get_next(r)

        if next.test_result_id is None:
            return None

        ret = SubmitToCheck()
        ret.test_result = next.test_result_id

        if next.test_result_id > 0:
            test_result = TestResult.objects.get(id=next.test_result_id)
            ret.test_data = test_result.test.data_get_map()
            ret.submit_data = test_result.submit.data_get_map()
        else:
            temporary_submit = TemporarySubmit.objects.get(id=-next.test_result_id)
            ret.test_data = temporary_submit.test_data_get_map()
            ret.submit_data = temporary_submit.submit_data_get_map()

        return ret


    @ExportMethod(NoneType, [long, TypedMap(unicode, AnonymousAttribute)], PCGlobal('JUDGE'))
    @staticmethod
    def set_partial_result(test_result_id, result):
        if test_result_id > 0:
            test_result = TestResult.objects.get(id=test_result_id)
            if test_result.tester != token_container.token.role:
                return
            test_result.oa_set_map(result)
        else:
            temporary_submit = TemporarySubmit.objects.get(id=-test_result_id)
            if temporary_submit.tester != token_container.token.role:
                return
            temporary_submit.result_set_map(result)

    @ExportMethod(NoneType, [long, TypedMap(unicode, AnonymousAttribute)], PCGlobal('JUDGE'))
    @staticmethod
    def set_result(test_result_id, result):
        if test_result_id > 0:
            test_result = TestResult.objects.get(id=test_result_id)
            if test_result.tester != token_container.token.role:
                return
            test_result.oa_set_map(result)
            test_result.pending = False
            test_result.save()
            RawEvent().send(Event(type='checking_checked_test_result', id=test_result.id))
        else:
            temporary_submit = TemporarySubmit.objects.get(id=-test_result_id)
            if temporary_submit.tester != token_container.token.role:
                return
            temporary_submit.result_set_map(result)
            temporary_submit.pending = False
            temporary_submit.save()
        
