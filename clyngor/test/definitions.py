"""Some definitions used for testing.

"""
import pytest
import clyngor
from functools import wraps


def run_with_clingo_binary_only(func):
    """Decorator deactivating clingo module handling before running
    the test function, then reactivating it if available.

    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        if clyngor.clingo_module_actived():
            clyngor.deactivate_clingo_module()
            ret = func(*args, **kwargs)
            clyngor.use_clingo_module()
        else:  # clingo module not here, so there is nothing to do
            ret = func(*args, **kwargs)
        return ret
    return wrapped


def run_with_clingo_module_only(func):
    """Decorator activating clingo module handling before running
    the test function, then deactivating it if available.

    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        was_using_module = clyngor.clingo_module_actived()
        clyngor.use_clingo_module()
        ret = func(*args, **kwargs)
        if not was_using_module:
            clyngor.use_clingo_binary()
        return ret
    return onlyif_clingo_module(wrapped)


def skipif_clingo_without_python(func):
    return pytest.mark.skipif(
        not clyngor.have_python_support(py3=True),
        reason="Require clingo with python3 support"
    )(func)


def skipif_no_clingo_module(func):
    return pytest.mark.skipif(
        not clyngor.have_clingo_module(),
        reason="Require official clingo module to be available"
    )(func)


# clearer names and oppositions
onlyif_clingo_module = skipif_no_clingo_module
onlyif_python_support = skipif_clingo_without_python

def onlyif_no_python_support(func):
    return pytest.mark.skipif(
        clyngor.have_python_support(py3=True),
        reason="Requires clingo not to support python"
    )(func)

def onlyif_no_clingo_module(func):
    return pytest.mark.skipif(
        clyngor.have_clingo_module(),
        reason="Require official clingo module to NOT be available"
    )(func)

