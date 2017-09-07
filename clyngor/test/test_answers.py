
import pytest
from clyngor.answers import Answers


@pytest.fixture
def simple_answers():
    return Answers((
        'a(0) b(1)',
        'c(2) d(3)',
        'e(4) f(5)',
        'g(6) h(7)',
    ))

@pytest.fixture
def noarg_answers():
    return Answers((
        '',
        'a',
        'b c',
        'd e f',
    ))


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


def test_tunning_first_arg_only(simple_answers):
    answers = simple_answers
    answers.first_arg_only
    assert next(answers) == {('a', 0), ('b', 1)}
    assert next(answers) == {('c', 2), ('d', 3)}
    assert next(answers) == {('e', 4), ('f', 5)}
