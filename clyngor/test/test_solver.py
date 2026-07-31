"""Tests of the Solver object, i.e. the explicit replacement of clyngor's
former module-level mutable state.

"""

import pytest

from clyngor.solver import (Solver, SolverUnavailableError,
                            AUTO, BINARY, MODULE)
from .definitions import (clingo_module_importable, clingo_binary_available,
                          skipif_no_clingo_binary, onlyif_clingo_module,
                          onlyif_no_clingo_module, onlyif_module_python_support)


UNREACHABLE = 'clingo-that-is-not-installed-anywhere'


def test_defaults():
    solver = Solver()
    assert solver.backend == AUTO
    assert solver.binary_path == 'clingo'


def test_invalid_backend_is_rejected_at_construction():
    with pytest.raises(ValueError):
        Solver(backend='pyclingo')

@pytest.mark.parametrize('path', ('', None, 42))
def test_invalid_binary_path_is_rejected_at_construction(path):
    with pytest.raises(ValueError):
        Solver(binary_path=path)


def test_solver_is_immutable():
    solver = Solver()
    with pytest.raises(Exception):  # FrozenInstanceError, a dataclasses detail
        solver.backend = MODULE

def test_using_returns_a_new_solver():
    solver = Solver()
    other = solver.using(backend=BINARY, binary_path='asprin')
    assert solver.backend == AUTO and solver.binary_path == 'clingo'
    assert other.backend == BINARY and other.binary_path == 'asprin'

def test_using_validates_too():
    with pytest.raises(ValueError):
        Solver().using(backend='nope')


def test_solvers_compare_by_value():
    assert Solver(backend=BINARY) == Solver(backend=BINARY)
    assert Solver(backend=BINARY) != Solver(backend=MODULE)
    assert len({Solver(), Solver()}) == 1  # hashable, since frozen


def test_module_availability_does_not_depend_on_the_backend():
    """The historical have_clingo_module() answered "is the module the
    active backend?" while reading like "is the module installed?"."""
    expected = clingo_module_importable()
    assert Solver(backend=BINARY).module_available is expected
    assert Solver(backend=MODULE).module_available is expected
    assert Solver(backend=AUTO).module_available is expected


def test_unreachable_binary_is_not_available():
    solver = Solver(backend=BINARY, binary_path=UNREACHABLE)
    assert not solver.binary_available
    assert solver.resolved_binary_path is None
    assert not solver.available

def test_unreachable_binary_raises_an_explicit_error():
    solver = Solver(backend=BINARY, binary_path=UNREACHABLE)
    with pytest.raises(SolverUnavailableError):
        solver.resolve()

@skipif_no_clingo_binary
def test_reachable_binary_resolves_to_binary():
    solver = Solver(backend=BINARY)
    assert solver.binary_available
    assert solver.resolved_binary_path.endswith('clingo')
    assert solver.resolve() == BINARY
    assert solver.uses_binary and not solver.uses_module


@onlyif_clingo_module
def test_module_backend_resolves_to_module():
    solver = Solver(backend=MODULE)
    assert solver.resolve() == MODULE
    assert solver.uses_module and not solver.uses_binary

@onlyif_no_clingo_module
def test_module_backend_raises_without_the_module():
    with pytest.raises(SolverUnavailableError):
        Solver(backend=MODULE).resolve()


@skipif_no_clingo_binary
def test_auto_prefers_the_binary():
    """Historical default, and the binary supports options the module
    path rejects (time_limit, constants)."""
    assert Solver(backend=AUTO).resolve() == BINARY

@onlyif_clingo_module
def test_auto_falls_back_to_the_module_when_no_binary():
    """The case that used to die on a bare FileNotFoundError: clingo
    pip-installed (which ships no executable), no binary anywhere."""
    solver = Solver(backend=AUTO, binary_path=UNREACHABLE)
    assert solver.resolve() == MODULE
    assert solver.available

def test_auto_without_any_backend_names_both_in_the_error():
    solver = Solver(backend=AUTO, binary_path=UNREACHABLE)
    if solver.module_available:
        pytest.skip("Require the clingo module NOT to be installed")
    with pytest.raises(SolverUnavailableError) as excinfo:
        solver.resolve()
    assert 'binary' in str(excinfo.value) and 'module' in str(excinfo.value)


@skipif_no_clingo_binary
def test_binary_version():
    version = Solver(backend=BINARY).version()
    assert version['clingo version'].startswith('5')

@onlyif_clingo_module
def test_module_version():
    """Used to raise UnboundLocalError: the module branch of
    clingo_version() read a name the binary branch bound below it."""
    version = Solver(backend=MODULE).version()
    assert version['clingo version'].startswith('5')

def test_version_of_an_unreachable_solver_raises_solver_unavailable():
    with pytest.raises(SolverUnavailableError):
        Solver(backend=BINARY, binary_path=UNREACHABLE).version()


@skipif_no_clingo_binary
def test_binary_support_probes_answer_a_boolean():
    solver = Solver(backend=BINARY)
    assert solver.has_python_support() in (True, False)
    assert solver.has_lua_support() in (True, False)

@onlyif_module_python_support
def test_module_python_support():
    assert Solver(backend=MODULE).has_python_support()

def test_support_probes_of_an_unreachable_binary_raise():
    """They used to answer False, conflating "no support" with "no
    solver at all"."""
    solver = Solver(backend=BINARY, binary_path=UNREACHABLE)
    with pytest.raises(SolverUnavailableError):
        solver.has_python_support()
    with pytest.raises(SolverUnavailableError):
        solver.has_lua_support()


@onlyif_clingo_module
def test_module_accessor_returns_the_clingo_module():
    import clingo
    assert Solver(backend=MODULE).module() is clingo

@onlyif_no_clingo_module
def test_module_accessor_raises_without_the_module():
    with pytest.raises(SolverUnavailableError):
        Solver(backend=MODULE).module()
