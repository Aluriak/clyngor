"""Various high level definition for client"""


import os
import tempfile
from clyngor import asp_parsing, parsing


def answer_set_to_str(answer_set:iter, atom_sep:str=' ') -> str:
    """Returns the string representation of given answer set.

    answer_set -- iterable of tuple (predicate, args)
    atom_sep -- string joining the atoms

    """
    return atom_sep.join(generate_answer_set_as_str(answer_set))


def generate_answer_set_as_str(answer_set:iter) -> iter:
    """Yield segment of string describing given answer set.

    answer_set -- iterable of tuple (predicate, args), or dict {predicate: [args]}

    """
    if isinstance(answer_set, dict):  # have been created using by_predicate, probably
        answer_set = (
            (predicate, args)
            for predicate, all_args in answer_set.items()
            for args in all_args
        )

    for predicate, args in answer_set:
        yield '{}({})'.format(predicate, ','.join(args)) if args else predicate


def answer_set_from_str(line:str, collapse_atoms:bool=False,
                        collapse_args:bool=True, parse_integer:bool=True) -> iter:
    """Yield atoms found in given string.

    line -- parsable string containing an answer set

    """
    yield from parsing.Parser(
        collapse_atoms=collapse_atoms,
        collapse_args=collapse_args,
        parse_integer=parse_integer
    ).parse_terms(line)


def save_answers_in_file(answers:iter, filename:str or None=None) -> str:
    """Return the name of the file in which the answer sets are written.

    answers -- iterable of answer set to write
    filename -- file to write ; if None, a temporary file will be created

    """
    if not filename:
        with tempfile.NamedTemporaryFile('w', delete=False) as ofd:
            filename = ofd.name
    with open(filename, 'w') as ofd:
        ofd.write('\n'.join(answer_set_to_str(answer) for answer in answers))
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
