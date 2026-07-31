"""The pre-1.0 way of choosing a backend was a set of module-level
toggles. They keep working on top of the default solver, and each of them
warns about what to use instead.

"""

import pytest

import clyngor
from clyngor import Solver

from .definitions import skipif_no_clingo_binary, onlyif_clingo_module


def test_use_clingo_binary_moves_the_default_solver():
    with pytest.deprecated_call():
        clyngor.use_clingo_binary('some-clingo-path')
    assert clyngor.default_solver() == Solver(backend='binary',
                                              binary_path='some-clingo-path')

def test_set_clingo_binary_keeps_the_backend():
    with clyngor.using_solver(backend='auto'):
        with pytest.deprecated_call():
            clyngor.set_clingo_binary('some-clingo-path')
        assert clyngor.default_solver() == Solver(backend='auto',
                                                  binary_path='some-clingo-path')

@onlyif_clingo_module
def test_use_clingo_module_moves_the_default_solver():
    with pytest.deprecated_call():
        clyngor.use_clingo_module()
    assert clyngor.default_solver().uses_module

def test_deactivate_clingo_module_moves_the_default_solver():
    with pytest.deprecated_call():
        clyngor.deactivate_clingo_module()
    assert clyngor.default_solver().backend == 'binary'


@skipif_no_clingo_binary
def test_clingo_bin_path_still_reads_and_assigns():
    """A module cannot intercept an assignment to itself unless its class
    does; without that, this one would silently write an attribute that
    nothing reads anymore."""
    with pytest.deprecated_call():
        assert clyngor.CLINGO_BIN_PATH == 'clingo'
    with pytest.deprecated_call():
        clyngor.CLINGO_BIN_PATH = '/usr/bin/clingo'
    assert clyngor.default_solver().binary_path == '/usr/bin/clingo'
    assert clyngor.command(('a.lp',))[0] == '/usr/bin/clingo'

def test_clingo_module_attributes_still_read():
    with pytest.deprecated_call():
        assert clyngor.clingo_module_available in (True, False)
    with pytest.deprecated_call():
        clyngor.clingo_module  # None unless the module is the active backend

def test_unknown_attribute_still_raises_attribute_error():
    with pytest.raises(AttributeError):
        clyngor.no_such_attribute


def test_probes_still_answer():
    with pytest.deprecated_call():
        assert clyngor.have_clingo_module() in (True, False)
    with pytest.deprecated_call():
        assert clyngor.clingo_module_actived() in (True, False)
    with pytest.deprecated_call():
        assert clyngor.load_clingo_module() in (True, False)
