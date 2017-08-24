
from clyngor import ASP, solve


def test_api_asp():

    answers = ASP("""
    rel(a,(c;d)). rel(b,(d;e)).
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    :- not obj(X):obj(X).
    :- not att(Y):att(Y).
    """)

    found = set()
    for answer in answers.by_predicate.sorted.first_arg_only:
        found.add(''.join(answer['obj']) + '×' + ''.join(answer['att']))
    assert found == {'a×cd', 'b×de', 'ab×d'}
