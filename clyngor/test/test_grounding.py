"""Testing of the decoupled grounding/solving API"""

import pytest
from clyngor import grounded_program, solve_from_grounded, solve as solve_standard, opt_models_from_clyngor_answers
from .definitions import clingo_noncompliant


@clingo_noncompliant
def test_simple():
    prg = '1{p(a;b;c)}1.'
    grounded = grounded_program(inline=prg)
    found = frozenset(solve_from_grounded(grounded))  # clingo module cannot be used here
    expected = frozenset(solve_standard(inline=prg))
    assert found == expected


@clingo_noncompliant
def test_with_opts():
    ASP = r"""
q(1..10).
1{p(X): q(X)}3.
nb(odd,N):- N={p(X): X\2=0}.
nb(even,N):- N={p(X): X\2=1}.
nb(sum,N):- N=#sum{X:p(X)}.
#minimize{N,2:nb(odd,N)}.
#maximize{N,1:nb(even,N)}.
    """
    grounded = grounded_program(inline=ASP)
    found = frozenset(opt_models_from_clyngor_answers(solve_from_grounded(grounded).by_predicate))
    expected = frozenset(opt_models_from_clyngor_answers(solve_standard(inline=ASP).by_predicate))
    assert found == expected
