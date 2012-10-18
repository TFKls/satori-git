# vim:ts=4:sts=4:sw=4:expandtab

"""
Compare helper procedures.
"""

from types import NoneType

CompareToCheck = Struct('CompareToCheck', (
    ('comparison_result', long, True),
    ('submit_data_1', TypedMap(unicode, AnonymousAttribute), False),
    ('submit_data_2', TypedMap(unicode, AnonymousAttribute), False),
))

@ExportClass
class Compare(object):
    """
    """
    @ExportMethod(CompareToCheck, [], PCGlobal('COMPARE'))
    @staticmethod
    def get_next():
        pass

    @ExportMethod(NoneType, [long, float], PCGlobal('COMPARE'))
    @staticmethod
    def set_result(comparison_result_id, result):
        pass
