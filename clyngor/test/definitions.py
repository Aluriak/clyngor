"""Some definitions used for testing.

Two orthogonal notions are distinguished here:

- the clingo module being *importable*: a property of the environment,
  fixed for the whole test session. This is what skip conditions rely on.
- the clingo module being *activated*: clyngor's global state, mutable at
  any time (and deactivated by default at import). This is what the
  run_with_* decorators manipulate, exception-safely, around each test.

Conflating the two is what made skip conditions misfire: clyngor starts
in binary mode, so have_clingo_module() is False at collection time even
when the module is installed.

"""
import importlib.util

import pytest
import clyngor
from functools import wraps


def clingo_module_importable() -> bool:
    """True if the official clingo module is installed, regardless of
    whether clyngor currently has it activated."""
    return importlib.util.find_spec('clingo') is not None


def run_with_clingo_binary_only(func):
    """Decorator deactivating clingo module handling while running
    the test function, then restoring the previous state.

    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        module_was_active = clyngor.clingo_module_actived()
        clyngor.deactivate_clingo_module()
        try:
            return func(*args, **kwargs)
        finally:
            if module_was_active:
                clyngor.use_clingo_module()
    return wrapped


def run_with_clingo_module_only(func):
    """Decorator activating clingo module handling while running
    the test function, then restoring the previous state.

    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        module_was_active = clyngor.clingo_module_actived()
        clyngor.use_clingo_module()
        try:
            return func(*args, **kwargs)
        finally:
            if not module_was_active:
                clyngor.deactivate_clingo_module()
    return onlyif_clingo_module(wrapped)


def skipif_clingo_without_python(func):
    return pytest.mark.skipif(
        not clyngor.have_python_support(py3=True),
        reason="Require clingo with python3 support"
    )(func)


def skipif_no_clingo_module(func):
    return pytest.mark.skipif(
        not clingo_module_importable(),
        reason="Require official clingo module to be installed"
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
        clingo_module_importable(),
        reason="Require official clingo module to NOT be installed"
    )(func)
