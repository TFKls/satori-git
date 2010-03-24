"""Miscellanea."""


import sys
import types


__all__ = (
    'Namespace',
    'flatten_coroutine',
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


def flatten_coroutine(coroutine):
    """Flattens a coroutine (inside, yielding another Generator    behaves like
    a sub-procedure call).
    """
    def run():
        stack = [coroutine]
        input = None
        error = None
        trace = None
        while len(stack) > 0:
            try:
                if error is None:
                    output = stack[-1].send(input)
                else:
                    output = stack[-1].throw(error)
                    error = None
                if isinstance(output, types.GeneratorType):
                    stack.append(output)
                    input = None
                else:
                    input = yield output
            except StopIteration:
                error = None
                input = None
                stack.pop()
            except Exception as ex:
                error = ex
                trace = sys.exc_traceback
                input = None
                stack.pop()
        if error is not None:
            raise error.__class__, error, trace
    return run()
