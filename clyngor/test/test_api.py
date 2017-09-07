
import tempfile
import pytest
import clyngor
from clyngor import ASP, solve, command
from clyngor import utils, CLINGO_BIN_PATH


@pytest.fixture
def asp_code():
    return """
    rel(a,(c;d)). rel(b,(d;e)).
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    :- not obj(X):obj(X).
    :- not att(Y):att(Y).
    """


def test_api_solve():
    files = []
    with tempfile.NamedTemporaryFile('wt', delete=False) as fd:
        fd.write('1 {a ; b ; c} 1 :- d.')
        files.append(fd.name)
    with tempfile.NamedTemporaryFile('wt', delete=False) as fd:
        fd.write('0 {d ; e} 1.')
        files.append(fd.name)
    answers = solve(files).no_arg
    print(answers.command)
    set = frozenset
    assert set(answers) == { set('da'), set('db'), set('dc'), set('e'), set() }


def test_api_command():
    files = ('a.lp', 'b.lp')
    cmd = command(files, nb_model=3)
    assert cmd == [CLINGO_BIN_PATH, *files, '-n 3']

    files = ('a.lp', 'b.lp', 'c')
    clyngor.CLINGO_BIN_PATH = '/usr/bin/clingo'  # NB: this have serious side effects. If any fail happen before the restauration, all other tests may fail.
    cmd = command(files, nb_model=0)
    clyngor.CLINGO_BIN_PATH = 'clingo'
    assert cmd == ['/usr/bin/clingo', *files, '-n 0']


def test_api_asp(asp_code):
    answers = ASP(asp_code)
    found = set()
    for answer in answers.by_predicate.sorted.first_arg_only:
        found.add(''.join(answer['obj']) + '×' + ''.join(answer['att']))
    assert found == {'a×cd', 'b×de', 'ab×d'}


def test_api_inline_by_solve(asp_code):
    answers = solve([], inline=asp_code)
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
