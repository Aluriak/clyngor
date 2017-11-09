
import pytest
from .test_api import asp_code  # fixture
from clyngor import solve


@pytest.fixture
def asp_code_with_constants():
    return """
    #const a=1.
    p(a).
    q(X):- p(X).
    """


def test_without_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (1,)


def test_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants,
                          constants={'a': 2}, print_command=True).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (2,)


# TODO: test solving.command
