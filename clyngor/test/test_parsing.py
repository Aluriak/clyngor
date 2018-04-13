import pytest

from clyngor import parsing
from clyngor.parsing import Parser


def test_simple_case():
    parsed = Parser().parse_clasp_output(OUTCLASP_SIMPLE.splitlines(),
                                         yield_stats=True, yield_info=True)
    models = []
    for type, payload in parsed:
        assert type in ('statistics', 'info', 'answer')
        if type == 'statistics':
            stats = payload
        elif type == 'answer':
            models.append(payload)
        else:
            assert type == 'info'
            info = payload
    assert len(models) == 2
    assert info == ('clasp version 3.2.0', 'Reading from stdin', 'Solving...', 'SATISFIABLE')
    assert stats == {'Models': '2', 'Calls': '1', 'CPU Time': '0.000s',
                     'Time': '0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)'}


def test_parse_termset_default():
    string = 'a(b,10) c(d("a",d_d),"v,v",c) d(-2,0)'
    expected = {
        ('a', ('b', 10)),
        ('c', ('d("a",d_d)', '"v,v"', 'c')),
        ('d', (-2, 0)),
    }
    assert Parser().parse_terms(string) == expected


def test_parse_termset():
    string = 'a(b,10) c(d("a",d_d),"v,v",c) d(-2,0)'
    expectation = {
        (False, True): {
            ('a', ('b', 10)),
            ('c', ('d("a",d_d)', '"v,v"', 'c')),
            ('d', (-2, 0)),
        },
        (False, False): {
            ('a', ('b', 10)),
            ('c', (('d', ('"a"', 'd_d')), '"v,v"', 'c')),
            ('d', (-2, 0)),
        },
        (True, True): {
            'a(b,10)',
            'c(d("a",d_d),"v,v",c)',
            'd(-2,0)',
        },
        # False True is expected to raise an Error (see dedicated function)
    }
    for parser_mode, expected in expectation.items():
        print(*parser_mode)
        assert    Parser(*parser_mode).parse_terms(string) == frozenset(expected)

def test_parse_termset_impossible():
    with pytest.raises(ValueError) as e_info:
        Parser(True, False)


def test_string():
    """Show that string with comma in it is handled correctly"""
    parsed = Parser().parse_clasp_output(OUTCLASP_STRING.splitlines())
    type, model = next(parsed)
    assert next(parsed, None) is None, "there is only one model"
    assert type == 'answer', "the model is an answer"
    assert len(model) == 1, "only 1 atom in it"
    pred, args = next(iter(model))
    assert pred == 'atom'
    assert args == ('","',)


def test_complex_atoms():
    parsed = Parser().parse_clasp_output(OUTCLASP_COMPLEX_ATOMS.splitlines())
    type, model = next(parsed)
    assert next(parsed, None) is None, "there is only one model"
    assert type == 'answer', "the model is an answer"
    assert len(model) == 3, "only 3 atoms in it"
    atoms = {atom[0]: atom for atom in model}
    assert set(atoms.keys()) == {'a', 'b', 'c'}


def test_optimization():
    parsed = Parser().parse_clasp_output(OUTCLASP_OPTIMIZATION.splitlines(), yield_stats=True)
    expected_stats = {
        'CPU Time': '0.130s',
        'Calls': '1',
        'Models': '1',
        'Optimization': '190',
        'Optimum': 'yes',
        'Threads': '4        (Winner: 2)',
        'Time': '0.051s (Solving: 0.03s 1st Model: 0.00s Unsat: 0.03s)'
    }
    for type, model in parsed:
        if type == 'statistics':
            assert model == expected_stats


def test_time_limit():
    parsed = Parser().parse_clasp_output(OUTCLASP_TIME_LIMIT.splitlines(),
                                         yield_stats=True,
                                         yield_info=True)
    expected_stats = {
        'TIME LIMIT': '1',
        'Models': '3+',
        'Optimum': 'unknown',
        'Optimization': '597301577',
        'Calls': '1',
        'Time': '4.000s (Solving: 2.82s 1st Model: 0.01s Unsat: 0.00s)',
        'CPU Time': '3.980s',
    }
    expected_info = tuple(OUTCLASP_TIME_LIMIT.splitlines()[:3] + ['SATISFIABLE'])
    expected_answer = iter((
        (('a', ()),), (('b', ()),), (('c', ()),)
    ))
    expected_optimization = iter((597337713, 597301761, 597301577))
    all_infos = []
    for type, model in parsed:
        if type == 'statistics':
            assert model == expected_stats
        elif type == 'info':
            assert model == expected_info
        elif type == 'answer':
            assert model == frozenset(next(expected_answer))
        elif type == 'optimization':
            assert model == (next(expected_optimization),)
        else:  # impossible
            assert False


def test_multiple_opt_values():
    parsed = Parser().parse_clasp_output(CLINGO_OUTPUT_MULTIPLE_OPT.splitlines())
    expected_answer = iter((
        (('a', ()),),
        (('b', ()),),
        (('c', ()),),
    ))
    expected_optimization = iter(((-10, 6), (-11, 6), (-13, 4)))
    all_infos = []
    for type, model in parsed:
        if type == 'statistics':
            assert False, 'no statistics'
        elif type == 'info':
            assert False, 'no info'
        elif type == 'answer':
            assert model == frozenset(next(expected_answer))
        elif type == 'optimization':
            assert model == next(expected_optimization)
        else:  # impossible
            assert False


def test_unsat():
    parsed = Parser().parse_clasp_output(OUTCLASP_UNSATISFIABLE.splitlines())
    assert next(parsed, None) is None


OUTCLASP_TIME_LIMIT = """clingo version 4.5.4
Reading from search.lp ...
Solving...
Answer: 1
a
Optimization: 597337713
Answer: 2
b
Optimization: 597301761
Answer: 3
c
Optimization: 597301577
SATISFIABLE

TIME LIMIT   : 1
Models       : 3+
  Optimum    : unknown
Optimization : 597301577
Calls        : 1
Time         : 4.000s (Solving: 2.82s 1st Model: 0.01s Unsat: 0.00s)
CPU Time     : 3.980s
"""

OUTCLASP_COMPLEX_ATOMS = """clasp version 3.2.0
Reading from stdin
Solving...
Answer: 1
a(b(1,"a")) b(42,12) c("42,12,a(23)",c)
SATISFIABLE

Models       : 1
Calls        : 1
Time         : 0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.000s
"""

OUTCLASP_STRING = """clasp version 3.2.0
Reading from test.lp
Solving...
Answer: 1
atom(",")
SATISFIABLE

Models       : 1
Calls        : 1
Time         : 0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.001s
"""

OUTCLASP_SIMPLE = """clasp version 3.2.0
Reading from stdin
Solving...
Answer: 1
a
Answer: 2
b
SATISFIABLE

Models       : 2
Calls        : 1
Time         : 0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.000s
"""

OUTCLASP_OPTIMIZATION = """clasp version 3.2.0
Reading from l.lp
Solving...
Answer: 1
set(2,9) set(2,10) score(20)
Optimization: 190
OPTIMUM FOUND

Models       : 1
  Optimum    : yes
Optimization : 190
Calls        : 1
Time         : 0.051s (Solving: 0.03s 1st Model: 0.00s Unsat: 0.03s)
CPU Time     : 0.130s
Threads      : 4        (Winner: 2)
"""

OUTCLASP_UNSATISFIABLE = """clasp version 3.2.0
Reading from l.lp
Solving...
UNSATISFIABLE

Models       : 0
Calls        : 1
Time         : 0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.000s
"""


CLINGO_OUTPUT_MULTIPLE_OPT = """
clingo version 5.2.2
Reading from ...ergrasp/ASPsources/findbestbiclique.lp ...
Solving...
Answer: 1
a
Optimization: -10 6
Answer: 2
b
Optimization: -11 6
Answer: 3
c
Optimization: -13 4
OPTIMUM FOUND

Models       : 3
  Optimum    : yes
Optimization : -13 4
Calls        : 1
Time         : 0.012s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.011s
"""
