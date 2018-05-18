"""Various high level definition for client"""


import os
import tempfile
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


def clingo_value_to_python(value:object) -> int or str or tuple:
    """Convert a clingo.Symbol object to the python equivalent"""
    if isinstance(value, (int, str)):
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


def answer_set_to_str(answer_set:iter, atom_sep:str=' ') -> str:
    """Returns the string representation of given answer set.

    answer_set -- iterable of tuple (predicate, args)
    atom_sep -- string joining the atoms

    """
    return atom_sep.join(generate_answer_set_as_str(answer_set))


def generate_answer_set_as_str(answer_set:iter, atom_end:str='') -> iter:
    """Yield segment of string describing given answer set.

    answer_set -- iterable of tuple (predicate, args), or dict {predicate: [args]}
    atom_end -- string added to the end of each given atom.

    >>> '.'.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ()))))
    'a(1,2).b'
    >>> ''.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ())), atom_end='.'))
    'a(1,2).b.'
    >>> '1'.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ())), atom_end='2'))
    'a(1,2)21b2'

    """
    if isinstance(answer_set, dict):  # have been created using by_predicate, probably
        answer_set = (
            (predicate, args)
            for predicate, all_args in answer_set.items()
            for args in all_args
        )

    template = '{}({})' + str(atom_end)
    for predicate, args in answer_set:
        if args:
            yield template.format(predicate, ','.join(map(str, args)))
        else:
            yield predicate + str(atom_end)


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
