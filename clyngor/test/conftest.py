"""Hooks for pytest.

"""

import pytest
import clyngor


@pytest.fixture(autouse=True)
def _restore_clyngor_global_state():
    """clyngor's module-level state (activated clingo module, binary path)
    is mutable and some tests legitimately flip it; make sure no test can
    leak its state into the next one, even by crashing."""
    module_was_active = clyngor.clingo_module_actived()
    bin_path = clyngor.CLINGO_BIN_PATH
    yield
    clyngor.CLINGO_BIN_PATH = bin_path
    if module_was_active and not clyngor.clingo_module_actived():
        clyngor.use_clingo_module()
    elif not module_was_active and clyngor.clingo_module_actived():
        clyngor.deactivate_clingo_module()


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
