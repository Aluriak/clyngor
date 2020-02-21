import pytest

from clyngor import parsing, answer_set_to_str
from clyngor.parsing import Parser


def test_careful_parsing_required():
    yeses = (
        'a(b(1)).',
        'a("hello ; a(b)").',
        'a("hello,b").',
        'a((1,2,3),4).',
    )
    nos = (
        'a(1,2,3).',
        'a(1,"hello",3).',
    )
    for yes in yeses:
        print('YES:', yes)
        assert     parsing.careful_parsing_required(yes)
    for no in nos:
        print('NO :', no)
        assert not parsing.careful_parsing_required(no)


def test_simple_case():
    parsed = Parser().parse_clasp_output(OUTCLASP_SIMPLE.splitlines(),
                                         yield_stats=True, yield_info=True)
    models = []
    for type, payload in parsed:
        assert type in ('statistics', 'info', 'answer', 'answer_number')
        if type == 'statistics':
            stats = payload
        elif type == 'answer':
            models.append(payload)
        elif type == 'answer_number':
            pass
        else:
            assert type == 'info'
            info = payload
    assert len(models) == 2
    assert info == ('clasp version 3.2.0', 'Reading from stdin', 'Solving...', 'SATISFIABLE')
    assert stats == {'Models': '2', 'Calls': '1', 'CPU Time': '0.000s',
                     'Time': '0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)'}

def test_parse_default_negation():
    string = '-r(1) -r(2)'
    expected = {
        ('-r', (1,)), ('-r', (2,)),
    }
    assert Parser().parse_terms(string) == expected


def test_parse_termset_default():
    string = r'a(b,10) c(d("a",d_d),"v,\"v\"",c) d(-2,0)'
    expected = {
        ('a', ('b', 10)),
        ('c', ('d("a",d_d)', r'"v,\"v\""', 'c')),
        ('d', (-2, 0)),
    }
    assert Parser().parse_terms(string) == expected

def test_parse_tuple():
    string = 'a(b,(2,3,(a,b)))'
    expected = {
        ('a', ('b', ('', (2, 3, ('', ('a', 'b')))))),
    }
    assert Parser().parse_terms(string) == expected

def test_parse_args_without_predicat():
    string = 'a((b,10)) c("",("",""))'
    expected = {
        ('a', (('', ('b', 10)),)),
        ('c', ('""', ('', ('""', '""')))),
    }
    assert Parser().parse_terms(string) == expected
    assert sorted(answer_set_to_str(expected).split()) == sorted(string.split())

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
    type, answer_number = next(parsed)
    assert type == 'answer_number'
    type, model = next(parsed)
    assert next(parsed, None) is None, "there is only one model"
    assert type == 'answer', "the model is an answer"
    assert len(model) == 1, "only 1 atom in it"
    pred, args = next(iter(model))
    assert pred == 'atom'
    assert args == ('","',)


def test_single_litteral():
    """Show that string with comma in it is handled correctly"""
    parsed = Parser().parse_clasp_output(OUTCLASP_SINGLE_LITERAL.splitlines())
    type, answer_number = next(parsed)
    assert type == 'answer_number'
    type, model = next(parsed)
    assert next(parsed, None) is None, "there is only one model"
    assert type == 'answer', "the model is an answer"
    assert len(model) == 2, "only 2 atom in it"
    assert model == {3, '"hello !"'}

def test_complex_atoms():
    parsed = Parser().parse_clasp_output(OUTCLASP_COMPLEX_ATOMS.splitlines())
    type, answer_number = next(parsed)
    assert type == 'answer_number'
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
    expected_info = iter((
        tuple(OUTCLASP_TIME_LIMIT.splitlines()[:3] + ['SATISFIABLE']),
    ))
    expected_answer = iter((
        (('a', ()),), (('b', ()),), (('c', ()),)
    ))
    expected_optimization = iter((597337713, 597301761, 597301577))
    for type, model in parsed:
        if type == 'statistics':
            assert model == expected_stats
        elif type == 'info':
            assert model == next(expected_info)
        elif type == 'answer':
            assert model == frozenset(next(expected_answer))
        elif type == 'answer_number':
            assert isinstance(model, int) and model > 0, model
        elif type == 'optimization':
            assert model == (next(expected_optimization),)
        elif type == 'progression':
            assert False, 'no progression'
        else:  # impossible
            assert False
    # ensure that all data has been found
    assert next(expected_info, None) is None
    assert next(expected_answer, None) is None
    assert next(expected_optimization, None) is None


def test_multiple_opt_values():
    parsed = Parser().parse_clasp_output(CLINGO_OUTPUT_MULTIPLE_OPT.splitlines())
    expected_answer = iter((
        (('a', ()),),
        (('b', ()),),
        (('c', ()),),
    ))
    expected_optimization = iter(((-10, 6), (-11, 6), (-13, 4)))
    for type, model in parsed:
        if type == 'statistics':
            assert False, 'no statistics'
        elif type == 'info':
            assert False, 'no info'
        elif type == 'answer':
            assert model == frozenset(next(expected_answer))
        elif type == 'answer_number':
            assert isinstance(model, int) and model > 0, model
        elif type == 'optimization':
            assert model == next(expected_optimization)
        elif type == 'optimum found':
            assert model == True
        else:  # impossible
            assert False
    # ensure that all data has been found
    assert next(expected_answer, None) is None
    assert next(expected_optimization, None) is None


def test_unsat():
    parsed = Parser().parse_clasp_output(OUTCLASP_UNSATISFIABLE.splitlines())
    assert next(parsed, None) is None


def test_multithread_with_progression():
    parsed = Parser().parse_clasp_output(CLINGO_OUTPUT_MULTITHREADING_WITH_PROGRESS.splitlines(),
                                         yield_prgs=True)
    expected_answer = iter((
        (('a', ()),),
        (('b', ()),),
    ))
    expected_progress = iter((
        '[   2;3299] (Error: 1648.5)',
    ))
    expected_optimization = iter(((3299,), (3296,)))
    for type, model in parsed:
        if type == 'statistics':
            assert False, 'no statistics'
        elif type == 'info':
            assert False, 'no info'
        elif type == 'answer':
            assert model == frozenset(next(expected_answer))
        elif type == 'answer_number':
            assert isinstance(model, int) and model > 0, model
        elif type == 'optimization':
            assert model == next(expected_optimization)
        elif type == 'progression':
            assert model == next(expected_progress)
        else:  # impossible
            assert False
    # ensure that all data has been found
    assert next(expected_answer, None) is None
    assert next(expected_progress, None) is None
    assert next(expected_optimization, None) is None


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

OUTCLASP_SINGLE_LITERAL = """clasp version 3.2.0
Reading from test.lp
Solving...
Answer: 1
3 "hello !"
SATISFIABLE

Models       : 1
Calls        : 1
Time         : 0.001s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.001s
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


CLINGO_OUTPUT_MULTITHREADING_WITH_PROGRESS = """
clingo version 5.2.2
Reading from ...rasp/powergrasp/asp/search-biclique.lp ...
/home/lbourneu/packages/powergrasp/powergrasp/asp/process-motif.lp:39:31-53: info: atom does not occur in any rule head:
  include_block(K,T,L,U)

Solving...
Answer: 1
a
Optimization: 3299
Progression : [   2;3299] (Error: 1648.5)
Answer: 2
b
Optimization: 3296
"""
