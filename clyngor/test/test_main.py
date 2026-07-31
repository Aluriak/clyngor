"""Test of the demo program of clyngor.__main__."""

from clyngor.__main__ import time_efficiency


def test_demo_program_runs():
    message = time_efficiency(number=1)
    assert 'Perform 1 calls' in message
