"""Various high level definition for client"""


import os
import math
import tempfile
import functools
from clyngor import parsing

try:
    import clingo
except ImportError:
    clingo = None


class ASPSyntaxError(SyntaxError):
    """This is a SyntaxError, but without the filename at the end of the
    string representation, and with a payload attached.

    Used by solving module to indicate problems in generated files.

    """
    def __init__(self, *args, payload:dict, **kwargs):
        super().__init__(*args, **kwargs)
        self.payload = payload

    def __str__(self):
        return self.msg

class ASPWarning(ValueError):
    """This is a ValueError, with a payload attached to it"""
    def __init__(self, msg:str, payload:dict):
        super().__init__(msg)
        self.payload = payload
        self.atom = payload['atom']


def parse_clingo_output(clingo_output:[str]):
    "Yield answer sets found in given clingo output"
    yield from (answer for anstype, answer
                in parsing.Parser().parse_clasp_output(clingo_output)
                if anstype == 'answer')


def make_hashable(val):
    """Convert lists and sets into tuples and frozensets

    >>> make_hashable(2)
    2
    >>> make_hashable('2')
    '2'
    >>> make_hashable([1, ({2, 3}, [4, 5], {(6, 7): [8, 9]})])
    (1, (frozenset({2, 3}), (4, 5), {(6, 7): (8, 9)}))

    """
    if isinstance(val, (tuple, list)):
        return tuple(map(make_hashable, val))
    elif isinstance(val, (frozenset, set)):
        return frozenset(map(make_hashable, val))
    elif isinstance(val, dict):
        return {make_hashable(k): make_hashable(v) for k, v in val.items()}
    return val


def remove_arguments_quotes(arguments:str):
    """Remove quotes at the beginning and at the end
    of the given arguments in ASP format.

    This function is used by the weak parser, and therefore
    does not need to meet robustness criterion.

    >>> remove_arguments_quotes('a,b')
    'a,b'
    >>> remove_arguments_quotes('"a","b"')
    'a,b'
    >>> remove_arguments_quotes('"a",b')
    'a,b'
    """
    def is_quoted(arg:str) -> bool:
        return (isinstance(arg, str) and len(arg) >= 2
                and arg[0] == '"' and arg[-1] == '"' and arg[-2] != '\\')
    return ','.join(arg[1:-1] if is_quoted(arg) else arg
                    for arg in arguments.split(','))


def clingo_value_to_python(value:object) -> int or str or tuple:
    """Convert a clingo.Symbol object to the python equivalent"""
    if str(type(value)) == 'clingo.Symbol':
        return clingo_symbol_as_python_value(value)
    elif isinstance(value, (int, str)):
        return value
    elif isinstance(value, (tuple, list)):
        return tuple(map(clingo_value_to_python, value))
    elif type(value).__name__ == 'Symbol':
        try:
            typename = str(value.type).lower()
            if typename == 'function':
                if value.arguments:
                    pyvalue = (value.name, tuple(map(clingo_value_to_python, value.arguments)))
                else:
                    pyvalue = value.name
            else:
                pyvalue = getattr(value, typename)
        except AttributeError as err:  # inf or sup
            if value.type == value.type.Infimum:
                return -math.inf
            elif value.type == value.type.Supremum:
                return math.inf
            else:
                raise err
        if typename == 'string':
            pyvalue = '"' + pyvalue.replace('"', '\\"') + '"'
        return pyvalue
    raise TypeError("Can't handle values like {} of type {}."
                    "".format(value, type(value)))


def clingo_symbol_as_python_value(term) -> object:
    "Convert a clingo.Symbol object to the python equivalent"
    if str(term.type) == 'Function':
        assert term.name is not None
        name = ('-' if term.negative else '') + term.name
        return (name, clingo_value_to_python(term.arguments))
    elif str(term.type) == 'String':
        assert term.name is None
        return ('"' + term.string + '"', ())
    elif str(term.type) == 'Number':
        assert term.name is None
        return (term.number, ())
    raise TypeError("Can't handle clingo.Symbol like {} of type {}."
                    "".format(value, type(value)))

def python_value_to_asp(val:str or int or list or tuple, *, args_of_predicate:bool=False) -> str or tuple:
    """Convert given python value in an ASP format"""
    if isinstance(val, (str, int)):
        return str(val) or '""'
    elif isinstance(val, float):
        return '"' + str(val) + '"'
    elif isinstance(val, tuple):
        assert len(val) == 2, "tuple value should be of size 2: (predicate, args))"
        predicate, args = val
        if args:
            return predicate + '(' + python_value_to_asp(list(args), args_of_predicate=bool(predicate)) + ')'
        else:  # no args
            return predicate
    elif isinstance(val, list):
        ender = ',' if len(val) == 1 and not args_of_predicate else ''
        return ','.join(map(python_value_to_asp, val)) + ender
    raise ValueError("Python value '{}' of type {} is not convertible in ASP.".format(repr(val), type(val)))
# python_value_to_asp.in_predicate = lambda x: python_value_to_asp(x, args_of_predicate=True)


def integers_to_string_atoms(model:iter) -> object:
    """Return an identical structure of (frozen)set, tuple and list, but with integer values as string"""
    if isinstance(model, (list, tuple, frozenset, set)):
        return type(model)(map(integers_to_string_atoms, model))
    elif isinstance(model, dict):
        return {integers_to_string_atoms(k): integers_to_string_atoms(v)
                for k, v in model.items()}
    elif isinstance(model, int):
        return str(model)
    else:
        return model


def answer_set_to_str(answer_set:iter, atom_end:str='', atom_sep:str=' ') -> str:
    """Returns the string representation of given answer set.

    answer_set -- iterable of tuple (predicate, args)
    atom_sep -- string joining the atoms

    """
    return atom_sep.join(generate_answer_set_as_str(answer_set, atom_end=atom_end))


def generate_answer_set_as_str(answer_set:iter, atom_end:str='') -> iter:
    """Yield segment of string describing given answer set.

    answer_set -- iterable of tuple (predicate, args), or dict {predicate: [args]}
    atom_end -- string added to the end of each given atom.

    >>> '.'.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ()))))
    'a(1,2).b'

    """
    if isinstance(answer_set, dict):  # have been created using by_predicate, probably
        answer_set = (
            (predicate, args)
            for predicate, all_args in answer_set.items()
            for args in all_args
        )

    template = '{}({})' + str(atom_end)
    for predicate, args in answer_set:
        yield python_value_to_asp((predicate, args)) + str(atom_end)


def answer_set_from_str(line:str, collapse_atoms:bool=False,
                        collapse_args:bool=True, parse_integer:bool=True) -> iter:
    """Yield atoms found in given string.

    line -- parsable string containing an answer set
    collapse_atoms -- whole atoms are left unparsed
    collapse_args -- atoms args are left unparsed
    parse_integer -- integers are returned as python int objects

    >>> tuple(sorted(answer_set_from_str('a b c d', True)))
    ('a', 'b', 'c', 'd')
    >>> tuple(sorted((answer_set_from_str('a b(a) c("text") d', True))))
    ('a', 'b(a)', 'c("text")', 'd')

    """
    yield from parsing.Parser(
        collapse_atoms=collapse_atoms,
        collapse_args=collapse_args,
        parse_integer=parse_integer
    ).parse_terms(line)


def save_answers_in_file(answers:iter, filename:str or None=None,
                         atom_separator:str=' ',
                         answer_separator:str='\n', end:str='') -> str:
    """Return the name of the file in which the answer sets are written.

    answers -- iterable of answer set to write
    filename -- file to write ; if None, a temporary file will be created
    atom_separator -- string placed between each atom
    answer_separator -- string placed between each answer set
    end -- string written at the end

    """
    if not filename:
        with tempfile.NamedTemporaryFile('w', delete=False) as ofd:
            filename = ofd.name
    with open(filename, 'w') as ofd:
        ofd.write(answer_separator.join(answer_set_to_str(answer, atom_sep=atom_separator)
                                        for answer in answers) + end)
    return filename


def load_answers_from_file(filename:str, answer_set_builder:type=frozenset) -> iter:
    """Yield answer set found in each line of given file"""
    with open(filename) as ifd:
        yield from (
            answer_set_builder(answer_set_from_str(line))
            for line in ifd
        )


def cleaned_path(path:str, error_if_invalid:bool=True) -> str:
    """Return the same path, but cleaned with user expension and absolute"""
    path = os.path.abspath(os.path.expanduser(path))
    if error_if_invalid and not os.path.exists(path):
        open(path)  # will raise FileExistsError
    return path


def with_clingo_bin(clingo_bin:str) -> callable:
    """Generate a wrapper where, during func call, the CLINGO_BIN_PATH clyngor
    variable is set of *clingo_bin*.

    Example:

        @with_clingo_bin('~/bin/clingo-3.2.1')
        def solve_problem(...):
            clyngor.solve(...)

    Not thread safe.

    """
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            import clyngor
            regular_bin, clyngor.CLINGO_BIN_PATH = clyngor.CLINGO_BIN_PATH, clingo_bin
            ret = func(*args, **kwargs)
            clyngor.CLINGO_BIN_PATH = regular_bin
            return ret
        return wrapped
    return wrapper


def opt_models_from_clyngor_answers(answers:iter):
    """Return generator of optimal models found by clingor.solve from answers.

    This function assumes that:

    - Option '--opt-mode=optN' have been given to clingo.

    - that models are yielded by clingo in increasing optimization value,
    therefore there is no need to verify that a model B succeeding a model A
    is better if they have different optimization value.

    """
    first_seen = False
    optimal_reached = False
    for model, opt, optimum, answer_number in answers.with_answer_number:
        if optimal_reached:
            yield model
        if answer_number == 1 and not first_seen:
            first_seen = True
        elif answer_number == 1:
            optimal_reached = True
            yield model
