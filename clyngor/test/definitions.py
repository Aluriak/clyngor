"""Some definitions used for testing.

"""
import clyngor
from functools import wraps


def clingo_noncompliant(func):
    """Decorator deactivating clingo module handling before running
    the test function, then reactivating it if available.

    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        clyngor.deactivate_clingo_module()
        ret = func(*args, **kwargs)
        clyngor.load_clingo_module()
        return ret
    return wrapped
