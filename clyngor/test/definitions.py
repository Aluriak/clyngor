"""Some definitions used for testing.

"""
import pytest
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


def skipif_clingo_without_python(func):
    decorator = pytest.mark.skipif(clyngor.have_python_support(py2=False),
                                   reason="Need clingo with python3 support")
    return decorator(func)
