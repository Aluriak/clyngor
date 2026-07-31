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


def binary_has_python_support() -> bool:
    """True if the clingo *binary* was compiled with python support."""
    return bool(clyngor.utils.try_python_availability_in_clingo_binary(py3=True))


def module_has_python_support() -> bool:
    """True if the clingo *module* can run embedded #script (python)."""
    if not clingo_module_importable():
        return False
    return bool(clyngor.utils.try_python_availability_in_clingo_module(py3=True))


def skipif_clingo_without_python(func):
    """NB: mode-specific, because binary and module support differ. This
    one is about the binary; module-mode tests want
    onlyif_module_python_support. Using clyngor.have_python_support()
    here would read whichever mode happens to be active at *collection*
    time, which is not the mode the test itself runs in."""
    return pytest.mark.skipif(
        not binary_has_python_support(),
        reason="Require a clingo binary with python3 support"
    )(func)


def onlyif_module_python_support(func):
    return pytest.mark.skipif(
        not module_has_python_support(),
        reason="Require the clingo module to support embedded python"
    )(func)


def onlyif_no_module_python_support(func):
    return pytest.mark.skipif(
        module_has_python_support(),
        reason="Require the clingo module NOT to support embedded python"
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
        binary_has_python_support(),
        reason="Requires the clingo binary not to support python"
    )(func)

def onlyif_no_clingo_module(func):
    return pytest.mark.skipif(
        clingo_module_importable(),
        reason="Require official clingo module to NOT be installed"
    )(func)
