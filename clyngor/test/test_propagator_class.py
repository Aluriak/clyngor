"""Tests the clyngor' Propagator class and the underlying API"""

import clyngor
from .definitions import skipif_clingo_without_python


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
    return not inputs[('b', (2,))]

constraint = Constraint(formula, {('b', (V,))})

# regular main function
main = Main(constraint)
#end.

1{b(X): X=1..3}1.
"""


class MyPropagator(clyngor.Propagator):

    def __init__(self):
        self.found_atoms = set()
        self.found_p = set()

    def on(self, predicate, *args):
        self.found_atoms[predicate].add(tuple(args))

    def on_p(self, only_arg):
        self.found_p.add(only_arg)


@skipif_clingo_without_python
def test_the_subclass():
    prop = MyPropagator.run_with(ASP_CODE)
    for answer in prop.answers:
        pass
    assert prop.found_p == {1, 2}
    assert prop.found_atoms == {'p': {(1,), (2,)}, 'q': {('a', 'b', 'p(1)')}}


@skipif_clingo_without_python
def test_pyconstraint():
    models = set(clyngor.solve(inline=PYCONSTRAINT_CODE))
    assert len(models) == 2
    assert models == {
        frozenset({('b', (1,))}),
        frozenset({('b', (3,))}),
    }
