
import random
import pytest
from clyngor import asp_parsing


@pytest.fixture
def asp_source_and_graph():
    return {
        """
        rel(a,c). rel(a,d). rel(b,d). rel(b,e).
        obj(X):- rel(X,_) ; rel(X,Y): att(Y).
        att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
        :- not obj(X):obj(X).
        :- not att(Y):att(Y).
        """: {
            4: {0, 1, 2, 3, 5},
            5: {0, 1, 2, 3, 4},
            6: {4},
            7: {5},
        },
        "a(1).  p(X):- a(X).": {1: {0}},
        "p(X):- a(X).  q(X):- p(X) ; q(X).": {1: {0, 1}},
    }.items()


def test_endpoints(asp_source_and_graph):
    sources, targets = asp_parsing.program_to_endpoints("a(1).  p(X):- a(X).")
    assert targets == {'a': {0}, 'p': {1}}
    assert sources == {'a': {1}}

    sources, targets = asp_parsing.program_to_endpoints("p(X):- a(X).  q(X):- p(X) ; q(X).")
    assert targets == {'p': {0}, 'q': {1}}
    assert sources == {'p': {1}, 'q': {1}, 'a': {0}}


def test_interdependency_graph(asp_source_and_graph):
    for source, expected in asp_source_and_graph:
        graph = asp_parsing.program_to_dependancy_graph(source)
        assert graph == expected
