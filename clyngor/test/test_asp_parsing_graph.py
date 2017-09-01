
import random
import pytest
from clyngor import asp_parsing


@pytest.fixture
def asp_source_and_graph():
    return """
    rel(a,c). rel(a,d). rel(b,d). rel(b,e).
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    :- not obj(X):obj(X).
    :- not att(Y):att(Y).
    """, {
        0: {4, 5}, 1: {4, 5}, 2: {4, 5}, 3: {4, 5},   # data nodes
        4: {5, 6},  # obj/1
        5: {4, 7},  # att/1
    }


def test_interdependency_graph(asp_source_and_graph):
    source, expected = asp_source_and_graph
    graph = asp_parsing.program_to_dependancy_graph(source)
    assert graph == expected
