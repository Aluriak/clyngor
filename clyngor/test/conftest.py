"""Hooks for pytest.

"""

import pytest
import clyngor


@pytest.fixture(autouse=True)
def _restore_clyngor_default_solver():
    """The default solver is module-level state and some tests legitimately
    replace it; make sure no test can leak its own into the next one, even
    by crashing."""
    solver = clyngor.default_solver()
    yield
    clyngor.set_default_solver(solver)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: this test is slow to execute"
    )

def pytest_addoption(parser):
    parser.addoption('--quick', action='store_true',
                     default=False, help='do not run slow tests')

def pytest_collection_modifyitems(config, items):
    if not config.getoption('--quick'):
        return
    # --quick given in cli: skip slow tests
    skip_slow = pytest.mark.skip(reason="remove --quick option to run")
    for item in items:
        if 'slow' in item.keywords:
            item.add_marker(skip_slow)
