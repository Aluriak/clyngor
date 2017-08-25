
import clyngor
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


def test_api_inline_by_solve():

    answers = solve([], inline="""
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


def test_string_with_lot_of_crap():
    dangerous_string = r'"\"1,3-dimethyl-2-[2-oxopropyl thio]imidazolium chloride\""'
    for sol in clyngor.ASP('atom({}).'.format(dangerous_string)).careful_parsing:
        assert len(sol) == 1
        pred, args = next(iter(sol))
        assert pred == 'atom'
        assert len(args) == 1
        assert args[0] == dangerous_string


def test_string_without_escaped_quotes():
    dangerous_string = r'"1,3-dimethyl-2-[2-oxopropyl thio]imidazolium chloride"'
    for sol in clyngor.ASP('atom({}).'.format(dangerous_string)).careful_parsing:
        assert len(sol) == 1
        pred, args = next(iter(sol))
        assert pred == 'atom'
        assert len(args) == 1
        assert args[0] == dangerous_string
