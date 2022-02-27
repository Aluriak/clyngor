
import pytest
from .test_api import asp_code  # fixture
import clyngor
from clyngor import solve
from .definitions import run_with_clingo_binary_only, run_with_clingo_module_only


@pytest.fixture
def asp_code_with_constants():
    return """
    #const a=1.
    p(a).
    q(X):- p(X).
    """


@run_with_clingo_binary_only
def test_without_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (1,)


@run_with_clingo_binary_only
def test_constants(asp_code_with_constants):
    answers = tuple(solve([], inline=asp_code_with_constants,
                          constants={'a': 2}, print_command=True).by_predicate)
    assert len(answers) == 1
    answer = answers[0]['q']
    assert len(answer) == 1
    assert next(iter(answer)) == (2,)


LITERALS_ARE_SHOWN = 'a.  link(a).  #show link/1.  #show 3. #show "hello !".'

@run_with_clingo_module_only
def test_literal_outputs_by_show():
    with pytest.raises(RuntimeError) as excinfo:
        # If this fails, there is some chance the clingo module
        #  now accepts litterals in output.
        answers = tuple(solve(inline=LITERALS_ARE_SHOWN).by_predicate)

@run_with_clingo_binary_only
def test_literal_outputs_by_show_working():
    answers = tuple(solve(inline=LITERALS_ARE_SHOWN).by_predicate)
    print(answers)
    assert len(answers) == 1
    answer = answers[0]
    print(answers)
    assert len(answer) == 3
    assert set(answer) == {'link', '"hello !"', 3}
    assert answer == {'link': {('a',)}, '"hello !"': {()}, 3: {()}}


# TODO: test solving.command
