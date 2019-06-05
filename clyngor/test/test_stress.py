"""Stress tests for clyngor.
"""

import pytest
from clyngor import solve
from .definitions import clingo_noncompliant


@pytest.mark.slow
@clingo_noncompliant
def test_many_call_to_test_file_closing():
    """at some point, if files are not closed, this should fail"""
    for idx in range(100):  # arbitrary number of call leading to an error
        models = solve(inline=f'a({idx}).', delete_tempfile=True, force_tempfile=True)  # force the use of tempfile
        assert next(models) == {('a', (idx,))}
        with pytest.raises(StopIteration):
            next(models)
