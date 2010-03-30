"""Miscellanea."""


import sys
import types


__all__ = (
    'Namespace',
    'flattenCoroutine',
)


class Namespace(dict):
    """A dictionary whose elements can be accessed as attributes.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __hasattr__(self, key):
        return key in self

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)


def flattenCoroutine(coroutine):
    """Flattens a coroutine (inside, yielding another Generator    behaves like
    a sub-procedure call).
    """
    def _flattened():
        stack = [coroutine]
        value = None
        error = None
        trace = None
        while len(stack) > 0:
            try:
                if error is None:
                    result = stack[-1].send(value)
                else:
                    result = stack[-1].throw(error)
                    error = None
                if isinstance(result, types.GeneratorType):
                    stack.append(result)
                    value = None
                else:
                    value = yield result
            except StopIteration:
                error = None
                value = None
                stack.pop()
            except Exception as ex:
                error = ex
                trace = sys.exc_traceback
                value = None
                stack.pop()
        if error is not None:
            raise error.__class__, error, trace
    return _flattened()
