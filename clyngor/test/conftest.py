"""Hooks for pytest.

"""

import pytest


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
