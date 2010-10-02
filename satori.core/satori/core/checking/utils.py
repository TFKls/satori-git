# vim:ts=4:sts=4:sw=4:expandtab

from django.db import transaction

def wrap_transaction_management(func):
    def new_func(*args, **kwargs):
        transaction.enter_transaction_management()
        try:
            return func(*args, **kwargs)
        finally:
            transaction.leave_transaction_management()
    return new_func

def wrap_transaction(func):
    def new_func(*args, **kwargs):
        transaction.enter_transaction_management()
        transaction.managed(True)
        try:
            ret = func(*args, **kwargs)
            transaction.commit()
        except:
            transaction.rollback()
            transaction.leave_transaction_management()
            raise
        else:
            transaction.leave_transaction_management()
            return ret
    return new_func

