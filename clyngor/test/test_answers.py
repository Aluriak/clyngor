
import pytest
from clyngor.answers import Answers


@pytest.fixture
def simple_answers():
    return Answers((
        'a(0) b(1)',
        'c(2) d(3)',
        'e(4) f(5)',
        'g(6) h(7)',
        'i j',
    ))

@pytest.fixture
def multiple_args():
    return Answers((
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
    ))

@pytest.fixture
def noarg_answers():
    return Answers((
        '',
        'a',
        'b c',
        'd e f',
    ))

@pytest.fixture
def many_atoms_answers():
    return Answers((
        'a b(4) b(3) a(1) vv(1) vv v(a) v(b)',
    ))

@pytest.fixture
def optimized_answers():
    return Answers((
        ('edge(4,"s…lp.") r_e_l(1,2)', 1),
        ('edge(4,"s…lp.") r_e_l(1,2)', 2),
        ('edge(4,"s…lp.") r_e_l(1,2)', 3),
        ('edge(4,"s…lp.") r_e_l(1,2)', 4),
    ), with_optimization=True)


def test_parsing_args_when_noargs(noarg_answers):
    answers = noarg_answers
    assert next(answers) == frozenset()
    assert next(answers) == {('a', ())}
    answers = noarg_answers.parse_args
    assert next(answers) == {('b', ()), ('c', ())}
    answers.by_predicate
    assert next(answers) == {'d': frozenset({()}), 'e': frozenset({()}),
                             'f': frozenset({()})}


def test_multiple_tunning_no_arg(noarg_answers):
    answers = noarg_answers.no_arg
    assert next(answers) == frozenset()
    assert next(answers) == {'a'}
    assert next(answers) == {'b', 'c'}
    answers.by_predicate
    assert next(answers) == {'d': frozenset(), 'e': frozenset(), 'f': frozenset()}


def test_multiple_tunning(simple_answers):
    answers = simple_answers
    assert next(answers) == {('a', (0,)), ('b', (1,))}
    answers.by_predicate
    assert next(answers) == {'c': {(2,)}, 'd': {(3,)}}
    answers.first_arg_only
    assert next(answers) == {'e': {4}, 'f': {5}}
    answers.int_not_parsed
    assert next(answers) == {'g': {'6'}, 'h': {'7'}}
    assert next(answers) == {'i': {()}, 'j': {()}}
    assert next(answers, None) is None


def test_tunning_first_arg_only(simple_answers):
    answers = simple_answers
    answers.first_arg_only
    assert next(answers) == {('a', 0), ('b', 1)}
    assert next(answers) == {('c', 2), ('d', 3)}
    assert next(answers) == {('e', 4), ('f', 5)}
    assert next(answers) == {('g', 6), ('h', 7)}
    assert next(answers) == {('i', ()), ('j', ())}
    assert next(answers, None) is None


def test_tunning_atoms_as_string_and_sorted_more_complex(many_atoms_answers):
    answers = many_atoms_answers.atoms_as_string.sorted
    assert next(answers) == tuple(sorted('a b(4) b(3) a(1) vv(1) vv v(a) v(b)'.split()))
    assert next(answers, None) is None


def test_tunning_atoms_as_string_and_sorted(simple_answers):
    answers = simple_answers.atoms_as_string.sorted
    assert next(answers) == ('a(0)', 'b(1)')
    assert next(answers) == ('c(2)', 'd(3)')
    assert next(answers) == ('e(4)', 'f(5)')
    assert next(answers) == ('g(6)', 'h(7)')
    assert next(answers) == ('i', 'j')
    assert next(answers, None) is None


def test_tunning_atoms_as_string(simple_answers):
    answers = simple_answers
    answers.atoms_as_string
    assert next(answers) == {'a(0)', 'b(1)'}
    assert next(answers) == {'c(2)', 'd(3)'}
    answers.careful_parsing
    assert next(answers) == {'e(4)', 'f(5)'}
    assert next(answers) == {'g(6)', 'h(7)'}
    assert next(answers) == {'i', 'j'}
    assert next(answers, None) is None


def test_multiple_args_in_atoms(multiple_args):
    answers = multiple_args
    assert next(answers) == {('edge', (4, '"s…lp."')), ('r_e_l', (1, 2))}
    answers = answers.atoms_as_string
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    answers.careful_parsing
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    assert next(answers, None) is None


def test_optimization_access(optimized_answers):
    answers = optimized_answers.with_optimization
    assert next(answers) == ({('edge', (4, '"s…lp."')), ('r_e_l', (1, 2))}, 1)
    answers = answers.no_arg
    assert next(answers) == ({'edge', 'r_e_l'}, 2)
    answers.atoms_as_string
    assert next(answers) == ({'edge(4,"s…lp.")', 'r_e_l(1,2)'}, 3)
