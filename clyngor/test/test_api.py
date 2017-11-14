
import tempfile
import pytest
import clyngor
from clyngor import ASP, solve, command
from clyngor import utils, CLINGO_BIN_PATH
from clyngor import asp_parsing


@pytest.fixture
def asp_code():
    return """
    rel(a,(c;d)). rel(b,(d;e)).
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    :- not obj(X):obj(X).
    :- not att(Y):att(Y).
    """


def test_api_solve_with_weird_flags():
    files = []
    with tempfile.NamedTemporaryFile('wt', delete=False) as fd:
        fd.write('1 {a ; b ; c} 1 :- d.')
        files.append(fd.name)
    with tempfile.NamedTemporaryFile('wt', delete=False) as fd:
        fd.write('0 {d ; e} 1.')
        files.append(fd.name)

    answers = solve(files, options='--parallel-mode=4').no_arg
    print(answers.command)
    set = frozenset
    assert set(answers) == { set('da'), set('db'), set('dc'), set('e'), set() }

    answers = solve(files, options='--opt-mode=optN').no_arg
    print(answers.command)
    set = frozenset
    assert set(answers) == { set('da'), set('db'), set('dc'), set('e'), set() }

    answers = solve(files, options='--parallel-mode=4 --opt-mode=optN').no_arg
    print(answers.command)
    set = frozenset
    assert set(answers) == { set('da'), set('db'), set('dc'), set('e'), set() }


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
    cmd = command(files, nb_model=3, stats=False)
    assert cmd == [CLINGO_BIN_PATH, *files, '-n 3']

    files = ('a.lp', 'b.lp', 'c')
    clyngor.CLINGO_BIN_PATH = '/usr/bin/clingo'  # NB: this have serious side effects. If any fail happen before the restauration, all other tests may fail.
    cmd = command(files, nb_model=0)
    clyngor.CLINGO_BIN_PATH = 'clingo'
    assert cmd == ['/usr/bin/clingo', '--stats', *files, '-n 0']


def test_api_asp(asp_code):
    answers = ASP(asp_code)
    found = set()
    for answer in answers.by_predicate.sorted.first_arg_only:
        found.add(''.join(answer['obj']) + '×' + ''.join(answer['att']))
    assert found == {'a×cd', 'b×de', 'ab×d'}


def test_api_inline_by_solve(asp_code):
    answers = solve((), inline=asp_code)
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


def test_add_debug_lines(asp_code):
    line_to_debug = 'natt(Y):- rel(_,Y) ; not rel(X,Y): obj(X).'
    debug = asp_parsing.debug.lines_for(line_to_debug, id=42)
    print('JLRBLI DEBUG:', debug)
    source = '\n'.join(asp_parsing.parsed_to_source(debug))
    print(source)
    assert source == """
ok(42).
head(42):- ap(42) ; not ko(42).
ap(42):- ok(42) ; rel(_,Y) ; not rel(X,Y): obj(X).
bl(42):- ok(42) ; not rel(_,Y).
bl(42):- ok(42) ; not not rel(X,Y): obj(X).
""".strip()


def test_no_input(capsys):
    """This test ensure that empty input do not lead the code to wait forever
    clingo to finish, since it will just wait for stdin input.

    So if this test takes time to run, you know why.

    Note the use of capsys fixture, allowing to disable the input patching
    that make it fail automatically, and therefore disturbing the functionality.

    """
    with capsys.disabled():
        assert tuple(clyngor.solve((), inline='')) == ()


def test_syntax_error():
    with pytest.raises(clyngor.ASPSyntaxError) as excinfo:
        tuple(clyngor.solve((), inline='invalid'))
    assert excinfo.value.filename.startswith('/tmp/tmp')
    assert excinfo.value.lineno == 2
    assert excinfo.value.offset == 1
    assert excinfo.value.payload['char_end'] == 2
    assert excinfo.value.msg.startswith('unexpected EOF in file /tmp/tmp')
    assert excinfo.value.msg.endswith(' at line 2 and column 1-2')


def test_undefined_warning():
    with pytest.raises(clyngor.ASPWarning) as excinfo:
        tuple(clyngor.solve((), inline='b:- c.', error_on_warning=True))
    assert excinfo.value.atom == 'c'
    assert len(excinfo.value.args) == 1
    start = "atom 'c' does not occur in any rule head in file /tmp/tmp"
    assert excinfo.value.args[0].startswith(start)
    assert excinfo.value.args[0].endswith(" at line 1 and column 5-6")

    # NB: the following should NOT raise any error (default value)
    tuple(clyngor.solve((), inline='b:- c.', error_on_warning=False))
    tuple(clyngor.solve((), inline='b:- c.'))
