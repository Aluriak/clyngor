

import pytest
import clyngor
from clyngor.upapi import converted_types


ASP_SOURCE = """

#script(python)

# Following lines are necessary to use the currently tested clyngor instead
#  of the one installed for the python version used by clingo.
# Note that the 0 index of sys.path is by convention a special one that should
#  not be modified, hence the insert in 1.
import sys
sys.path.insert(1, '.')

from clyngor import converted_types

@converted_types
def f(a:str, b:int, c:int):
    yield a * b
    yield b * c
    yield b + c

@converted_types
def g(a:str, b:int) -> tuple:  # the tuple make the return value an iterable of arguments
    yield a * b
    yield len(a) * b

@converted_types
def h(a:str, b:int) -> 'b'.join:  # any callable will be applied on function output
    for _ in range(b):
        yield a
#end.

p(X):- (X)=@f("hello",2,3).
p(X):- (X)=@f(2,2,3).  % this is a bad type, and therefore ignored

q(X,Y):- (X,Y)=@g("a",2).

r(X):- (X)=@h("a",4).

"""


def test_basic_decorator_usage():
    models = tuple(clyngor.solve(inline=ASP_SOURCE).by_predicate)
    assert len(models) == 1
    model = models[0]
    assert model == {
        'p': frozenset({('"hellohello"',), (6,), (5,)}),
        'q': frozenset({('"aa"', 2)}),
        'r': frozenset({('"abababa"',)}),
    }
