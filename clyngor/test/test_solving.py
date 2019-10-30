
import pytest
from .test_api import asp_code  # fixture
import clyngor
from clyngor import solve
from .definitions import clingo_noncompliant


@pytest.fixture
def asp_code_with_constants():
    return """
    #const a=1.
    p(a).
    q(X):- p(X).
    """


@clingo_noncompliant
def test_without_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (1,)


@clingo_noncompliant
def test_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants,
                          constants={'a': 2}, print_command=True).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (2,)


def test_restricted_and_literal_outputs():
    asp_code = 'a.  link(a).  #show link/1.  #show 3. #show "hello !".'
    answers = tuple(solve([], inline=asp_code).by_predicate)
    assert len(answers) == 1
    answer = answers[0]
    print(answers)
    assert len(answer) == 3
    assert set(answer) == {'link', 3, '"hello !"'}
    assert answer == {'link': {('a',)}, 3: {()}, '"hello !"': {()}}


# TODO: test solving.command
