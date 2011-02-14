# vim:ts=4:sts=4:sw=4:expandtab
import logging

class AccumulatorBase(object):
    def __init__(self, test_suite_result):
        super(AccumulatorBase, self).__init__()
        self.test_suite_result = test_suite_result

    def init(self):
        pass

    def accumulate(self, test_result):
        pass

    def status(self):
        return True

    def deinit(self):
        pass


accumulators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AccumulatorBase) and (item != AccumulatorBase):
        accumulators[item.__name__] = item
