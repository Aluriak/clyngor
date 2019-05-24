"""Testing of the decoupled grounding/solving API"""

import pytest
from clyngor import grounded_program, solve_from_grounded, solve as solve_standard


def test_simple():
    prg = '1{p(a;b;c)}1.'
    grounded = grounded_program(inline=prg)
    found = frozenset(solve_from_grounded(grounded))
    expected = frozenset(solve_standard(inline=prg))
    assert found == expected

