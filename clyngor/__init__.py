CLINGO_BIN_PATH = 'clingo'

from clyngor.utils import ASPSyntaxError, ASPWarning
from clyngor.answers import Answers, ClingoAnswers
from clyngor.propagator import Propagator
from clyngor.solving import solve, clingo_version, command
from clyngor.inline import ASP


def load_clingo_module() -> bool:
    try:
        import clingo as clingo_module
    except ImportError:
        clingo_module = None
    globals()['clingo_module'] = clingo_module

def have_clingo_module() -> bool:
    return clingo_module is not None

load_clingo_module()
