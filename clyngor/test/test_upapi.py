

import pytest
import clyngor
from clyngor.upapi import converted_types
from .definitions import onlyif_python_support


ASP_BASIC = """
#script(python)
from clyngor import converted_types
@converted_types
def h(a:str, b: int):
    return a*b
#end.
r(@h("s", 2)).
"""

ASP_DOUBLE_ARGS = """
#script(python)
from clyngor import converted_types
@converted_types
def g(a:str, b:int) -> tuple:  # the tuple make the return value an iterable of arguments
    yield a * b
    yield len(a) * b
#end.
q(X,Y):- (X,Y)=@g("a",2).
"""

ASP_ALL = """
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

@onlyif_python_support
def test_all_decorator_usage():
    models = tuple(clyngor.solve(inline=ASP_ALL).by_predicate)
    print(ASP_ALL)
    assert len(models) == 1
    model = models[0]
    assert model == {
        'p': frozenset({('"hellohello"',), (6,), (5,)}),
        'q': frozenset({('"aa"', 2)}),
        'r': frozenset({('"abababa"',)}),
    }

@onlyif_python_support
def test_basic_decorator_usage():
    models = tuple(clyngor.solve(inline=ASP_BASIC).by_predicate)
    print(ASP_BASIC)
    assert len(models) == 1
    model = models[0]
    assert model == {
        'r': frozenset({('"ss"',)}),
    }

@onlyif_python_support
def test_double_args_support():
    models = tuple(clyngor.solve(inline=ASP_DOUBLE_ARGS).by_predicate)
    print(ASP_DOUBLE_ARGS)
    assert len(models) == 1
    model = models[0]
    assert model == {
        'q': frozenset({('"aa"', 2)}),
    }
