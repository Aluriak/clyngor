__version__ = '0.5.2'

import sys as _sys
from types import ModuleType as _ModuleType
from contextlib import contextmanager as _contextmanager

from clyngor.solver import Solver, SolverUnavailableError
from clyngor.utils import ASPSyntaxError, ASPWarning, parse_clingo_output, clingo_value_to_python, with_clingo_bin, opt_models_from_clyngor_answers, answer_set_to_str, answer_set_from_str, try_python_availability_in_clingo, try_lua_availability_in_clingo
from clyngor.answers import Answers, ClingoAnswers
from clyngor.solving import solve, clingo_version, command
from clyngor.grounding import solve_from_grounded, grounded_program
from clyngor.inline import ASP
from clyngor.decoder import decode
from clyngor.propagators import Propagator, Variable, Main, Constraint


# The solver used by clyngor's module-level entry points when none is
# given. Everything that used to be spread over CLINGO_BIN_PATH and
# clingo_module now lives here, in one validated place; pass a Solver to
# solve() (or use using_solver) rather than reaching for this one.
_DEFAULT_SOLVER = Solver()


def default_solver() -> Solver:
    "Return the Solver used when none is given explicitly"
    return _DEFAULT_SOLVER

def set_default_solver(solver:Solver) -> Solver:
    """Make *solver* the one used when none is given, and return the
    previous one, so that callers can restore it."""
    global _DEFAULT_SOLVER
    if not isinstance(solver, Solver):
        raise TypeError("A Solver instance is expected, not {!r}".format(solver))
    previous, _DEFAULT_SOLVER = _DEFAULT_SOLVER, solver
    return previous

@_contextmanager
def using_solver(solver:Solver=None, **changes):
    """Context manager making *solver* the default one for its duration.

    Any Solver field can be given as a keyword instead, to derive from
    the current default:

        with clyngor.using_solver(backend='module'):
            ...

    Not thread safe — it moves module-level state. Passing a Solver to
    solve() is the thread-safe way to do this.

    """
    solver = default_solver() if solver is None else solver
    if changes:
        solver = solver.using(**changes)
    previous = set_default_solver(solver)
    try:
        yield solver
    finally:
        set_default_solver(previous)


def get_clingo_binary() -> str or None:
    "Return the path to the binary of the default solver, if reachable"
    return default_solver().resolved_binary_path

def have_python_support(py3:bool=True) -> bool or None:
    """True if clingo supports python 3 (or 2 if py3 is falsy).
    None if no python support at all."""
    return try_python_availability_in_clingo(py3)

def have_lua_support() -> bool:
    """True if clingo supports lua"""
    return try_lua_availability_in_clingo()


# The pre-1.0 interface to that state: mutators of module-level globals.
# Kept working on top of the default solver, since they are what all
# existing code calls, but they remain what they always were -- a
# process-wide toggle nothing validates the interaction of.

def load_clingo_module() -> bool:
    "True if the clingo module is importable"
    return default_solver().module_available

def have_clingo_module() -> bool:
    "True if the default solver goes through the clingo module"
    return default_solver().uses_module

def clingo_module_actived() -> bool:
    "True if the default solver goes through the clingo module"
    return default_solver().uses_module

def deactivate_clingo_module():
    "Make the default solver use the clingo binary"
    set_default_solver(default_solver().using(backend='binary'))

def use_clingo_module():
    "Make the default solver use the clingo module"
    solver = default_solver().using(backend='module')
    solver.resolve()  # raises SolverUnavailableError (a RuntimeError) if absent
    set_default_solver(solver)

def use_clingo_binary(path:str=None):
    "Make the default solver use the clingo binary found at *path*"
    solver = default_solver().using(backend='binary')
    set_default_solver(solver.using(binary_path=path) if path else solver)

def set_clingo_binary(path:str):
    "Set the binary path of the default solver"
    set_default_solver(default_solver().using(binary_path=path))


class _ClyngorModule(_ModuleType):
    """Keeps the pre-1.0 module attributes working.

    `clyngor.CLINGO_BIN_PATH = path` was a documented way to point clyngor
    at a binary, and a module cannot intercept an assignment to itself
    unless its class does — without this, such an assignment would
    silently write an attribute nobody reads anymore.

    """

    def __getattr__(self, name):
        if name == 'CLINGO_BIN_PATH':
            return default_solver().binary_path
        if name == 'clingo_module':
            solver = default_solver()
            return solver.module() if solver.uses_module else None
        if name == 'clingo_module_available':
            return default_solver().module_available
        raise AttributeError("module {!r} has no attribute {!r}"
                             "".format(__name__, name))

    def __setattr__(self, name, value):
        if name == 'CLINGO_BIN_PATH':
            set_clingo_binary(value)
        else:
            super().__setattr__(name, value)


_sys.modules[__name__].__class__ = _ClyngorModule


# last, clyngor depending modules
from clyngor.upapi import converted_types, converted_types_or_symbols
