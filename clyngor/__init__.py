CLINGO_BIN_PATH = 'clingo'
__version__ = '0.3.8'

from clyngor.utils import ASPSyntaxError, ASPWarning, clingo_value_to_python
from clyngor.answers import Answers, ClingoAnswers
from clyngor.solving import solve, clingo_version, command
from clyngor.inline import ASP
from clyngor.upapi import converted_types, converted_types_or_symbols
from clyngor.propagators import Propagator, Variable, Main, Constraint


def load_clingo_module() -> bool:
    try:
        import clingo as clingo_module
    except ImportError:
        clingo_module = None
    globals()['clingo_module'] = clingo_module

def have_clingo_module() -> bool:
    return clingo_module is not None

def deactivate_clingo_module():
    globals()['clingo_module'] = None

load_clingo_module()


def have_python_support(py2:bool=True, py3:bool=True) -> bool or None:
    """True if clingo supports python for given versions.
    None if no python support at all."""
    py_ver = clingo_version()['python']
    if py_ver:
        return (py2 and py_ver.startswith('2')) or (py3 and py_ver.startswith('3'))

def have_lua_support() -> bool:
    """True if clingo supports lua"""
    return bool(clingo_version()['lua'])
