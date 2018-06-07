"""Tests the clyngor' Propagator class and the underlying API"""

import clyngor
from .definitions import skipif_clingo_without_python, skipif_no_clingo_module


ASP_CODE = """
p(1).
p(X):- p(X-1) ; X<3.
q(a,b,p(1)).
"""

PYCONSTRAINT_CODE = """
#script(python)
from clyngor import Constraint, Variable as V, Main

# Build the constraint on atom b
def formula(inputs) -> bool:
    return inputs['b', (2,)]

constraint = Constraint(formula, {('b', (V,))})

# regular main function
main = Main(propagators=constraint)

#end.

1{b(1..3)}1.
"""


class MyPropagator(clyngor.Propagator):

    def __init__(self):
        super().__init__(follow=(('p', [...]), ('q', [...]*3)))
        self.found_atoms = {}

    def on_all_input(self, values:dict):
        for (pred, args), holds in values.items():
            if holds:
                self.found_atoms.setdefault(pred, set()).add(args)


@skipif_no_clingo_module
@skipif_clingo_without_python
def test_the_subclass():
    prop = MyPropagator()
    ctl = prop.run_with(inline=ASP_CODE)
    for answer in ctl:
        pass
    assert prop.found_atoms == {'p': {(1,), (2,)}, 'q': {('a', 'b', ('p', (1,)))}}


@skipif_clingo_without_python
def test_pyconstraint_from_embedded_code():
    models = set(clyngor.solve(inline=PYCONSTRAINT_CODE, use_clingo_module=False))
    assert len(models) == 2
    assert models == {
        frozenset({('b', (1,))}),
        frozenset({('b', (3,))}),
    }


@skipif_no_clingo_module
@skipif_clingo_without_python
def test_local_propagator_hidden_by_clingo():
    """Prove that main function (and therefore locally defined propagators)
    is ignored from code if called with clingo module
    """
    clingo_models = set(clyngor.solve(inline=PYCONSTRAINT_CODE, use_clingo_module=True))
    clyngor_models = set(clyngor.solve(inline=PYCONSTRAINT_CODE, use_clingo_module=False))
    assert len(clingo_models) == 3
    assert len(clyngor_models) == 2
    assert clingo_models == {
        frozenset({('b', (1,))}),
        frozenset({('b', (2,))}),
        frozenset({('b', (3,))}),
    }
    assert clyngor_models == {
        frozenset({('b', (1,))}),
        frozenset({('b', (3,))}),
    }


@skipif_no_clingo_module
@skipif_clingo_without_python
def test_pyconstraint_from_python():
    from clyngor import Constraint, Variable as V
    def formula(inputs) -> bool:
        return inputs['b', (2,)]
    constraint = Constraint(formula, {('b', (V,))})
    models = set(constraint.run_with(inline='1{b(1..3)}1.'))
    assert len(models) == 2
    assert models == {
        frozenset({('b', (1,))}),
        frozenset({('b', (3,))}),
    }
