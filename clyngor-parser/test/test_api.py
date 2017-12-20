
import pytest
import clyngor_parser


@pytest.fixture
def asp_code():
    return """
    rel(a,(c;d)). rel(b,(d;e)).
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    :- not obj(X):obj(X).
    :- not att(Y):att(Y).
    """


def test_add_debug_lines(asp_code):
    line_to_debug = 'natt(Y):- rel(_,Y) ; not rel(X,Y): obj(X).'
    debug = clyngor_parser.debug.lines_for(line_to_debug, id=42)
    print('JLRBLI DEBUG:', debug)
    source = '\n'.join(clyngor_parser.parsed_to_source(debug))
    print(source)
    assert source == """
ok(42).
head(42):- ap(42) ; not ko(42).
ap(42):- ok(42) ; rel(_,Y) ; not rel(X,Y): obj(X).
bl(42):- ok(42) ; not rel(_,Y).
bl(42):- ok(42) ; not not rel(X,Y): obj(X).
""".strip()
