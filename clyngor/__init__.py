CLINGO_BIN_PATH = 'clingo'
__version__ = '0.4.3'

from clyngor.utils import ASPSyntaxError, ASPWarning, parse_clingo_output, clingo_value_to_python, with_clingo_bin, opt_models_from_clyngor_answers, answer_set_to_str, answer_set_from_str
from clyngor.answers import Answers, ClingoAnswers
from clyngor.solving import solve, clingo_version, command
from clyngor.grounding import solve_from_grounded, grounded_program
from clyngor.inline import ASP
from clyngor.decoder import decode
from clyngor.propagators import Propagator, Variable, Main, Constraint


def load_clingo_module() -> bool:
    global clingo_module, clingo_module_available
    try:
        import clingo
        clingo_module = clingo
        clingo_module_available = True
    except ImportError:
        clingo_module = None
        clingo_module_available = False

def have_clingo_module() -> bool:
    return clingo_module is not None

def deactivate_clingo_module():
    global clingo_module
    clingo_module = None

def clingo_module_actived() -> bool:
    return clingo_module is not None

def use_clingo_module():
    if clingo_module is None:
        load_clingo_module()
    if clingo_module is None:  # loading didn't succeed
        raise RuntimeError("Clingo module was asked to be used (call to use_clingo_module), but it is not available.")

def use_clingo_binary(path=None):
    deactivate_clingo_module()
    set_clingo_binary(path or CLINGO_BIN_PATH)

def set_clingo_binary(path):
    globals()['CLINGO_BIN_PATH'] = path

def get_clingo_binary() -> str:
    import shutil
    return shutil.which(globals()['CLINGO_BIN_PATH'])

def have_python_support(py3:bool=True) -> bool or None:
    """True if clingo supports python 3 (or 2 if py3 is falsy).
    None if no python support at all."""
    return utils.try_python_availability_in_clingo(py3)

def have_lua_support() -> bool:
    """True if clingo supports lua"""
    return utils.try_lua_availability_in_clingo(py3)
    return bool(clingo_version()['lua'])


load_clingo_module()  # just initialize clingo module state, whether it is available or not
use_clingo_binary()  # use binary by default
# use_clingo_module()  # use module by default

if CLINGO_BIN_PATH != 'clingo':
    assert get_clingo_binary() == CLINGO_BIN_PATH


# last, clyngor depending modules
from clyngor.upapi import converted_types, converted_types_or_symbols
