"""Tests the clyngor' Propagator class and the underlying API"""

import clyngor


ASP_CODE = """
p(1).
p(X):- p(X-1) ; X<3.
q(a,b,p(1)).
"""


class MyPropagator(clyngor.Propagator):

    def __init__(self):
        self.found_atoms = set()
        self.found_p = set()

    def on(self, predicate, *args):
        self.found_atoms[predicate].add(tuple(args))

    def on_p(self, only_arg):
        self.found_p.add(only_arg)


def test_the_subclass():
    prop = MyPropagator.run_with(ASP_CODE)
    for answer in prop.answers:
        pass
    assert prop.found_p == {1, 2}
    assert prop.found_atoms == {'p': {(1,), (2,)}, 'q': {('a', 'b', 'p(1)')}}
