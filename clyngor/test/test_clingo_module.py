
import pytest
import clyngor
from .definitions import onlyif_clingo_module, onlyif_no_clingo_module, onlyif_python_support, onlyif_no_python_support, run_with_clingo_module_only, run_with_clingo_binary_only

@run_with_clingo_module_only
@onlyif_clingo_module
def test_basic_example():
    "Example taken from clingo module documentation: https://potassco.org/clingo/python-api/5.5/clingo/index.html"
    from clingo.symbol import Number
    from clingo.control import Control
    class Context:
        def inc(self, x):
            return Number(x.number + 1)
        def seq(self, x, y):
            return [x, y]

    def on_model(m):
        print(repr(m), m, dir(m))
        assert False, "Clingo module seems to have python support. Some test on the output model are to be done (just be sure there is a `a` atom). Model: " + repr(m)
        assert clyngor.have_python_support()

    ctl = Control()
    try:
        ctl.add("base", [], "a. #script(python) #end.")
    except RuntimeError as err:  # case where python support is not implemented
        assert err.args == ('<block>:1:4-25: error: python support not available\n',)
        assert not clyngor.have_python_support()
    else:  # python support available
        ctl.ground([("base", [])], context=Context())
        ctl.solve(on_model=on_model)


@run_with_clingo_module_only
@onlyif_clingo_module
@onlyif_python_support
def test_clingo_module_detection_and_state_MP():
    assert clyngor.utils.try_python_availability_in_clingo()
    assert clyngor.utils.try_python_availability_in_clingo_module()

@run_with_clingo_module_only
@onlyif_clingo_module
@onlyif_no_python_support
def test_clingo_module_detection_and_state_MnP():
    assert not clyngor.utils.try_python_availability_in_clingo()
    assert not clyngor.utils.try_python_availability_in_clingo_module()

@run_with_clingo_binary_only
@onlyif_no_clingo_module
@onlyif_python_support
def test_clingo_module_detection_and_state_BP():
    assert     clyngor.utils.try_python_availability_in_clingo()
    assert     clyngor.utils.try_python_availability_in_clingo_binary()

@run_with_clingo_binary_only
@onlyif_no_clingo_module
@onlyif_no_python_support
def test_clingo_module_detection_and_state_BnP():
    assert not clyngor.utils.try_python_availability_in_clingo()
    assert not clyngor.utils.try_python_availability_in_clingo_binary()
    with pytest.raises(ImportError):
        clyngor.utils.try_python_availability_in_clingo_module()

