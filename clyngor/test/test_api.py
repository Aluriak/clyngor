
import tempfile
import pytest
import clyngor
from clyngor import ASP, solve, command
from clyngor import utils, CLINGO_BIN_PATH
from .definitions import clingo_noncompliant


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
    assert cmd == [CLINGO_BIN_PATH, '-n 3', *files]

    cmd = command(files, nb_model=None)
    assert cmd == [CLINGO_BIN_PATH, '--stats', *files]

    files = ('a.lp', 'b.lp', 'c')
    clyngor.CLINGO_BIN_PATH = '/usr/bin/clingo'  # NB: this have serious side effects. If any fail happen before the restauration, all other tests may fail.
    cmd = command(files, nb_model=0)
    clyngor.CLINGO_BIN_PATH = 'clingo'
    assert cmd == ['/usr/bin/clingo', '-n 0', '--stats', *files]


def test_api_asp(asp_code):
    answers = ASP(asp_code)
    found = set()
    for answer in answers.by_predicate.sorted.first_arg_only:
        found.add(''.join(answer['obj']) + '×' + ''.join(answer['att']))
    assert found == {'a×cd', 'b×de', 'ab×d'}
    assert len(answers.statistics) == 4
    assert answers.statistics['Calls'] == '1'
    assert answers.statistics['Models'] == '3'
    assert set(answers.statistics.keys()) == {'CPU Time', 'Calls', 'Models', 'Time'}


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


def test_lispy_construct():
    dangerous_string = r'"1,3-dimethyl-2-[2-oxopropyl thio]imidazolium chloride"'
    source = r'atom((((a,b),c),d),{},(1,(2,3))). yield(X,Y,Z):- atom(X,Y,Z).'.format(dangerous_string)
    for sol in clyngor.ASP(source).careful_parsing.by_predicate.parse_args:
        assert len(sol) == 2
        assert sol['atom'] == sol['yield']
        args = next(iter(sol['yield']))
        assert len(args) == 3
        assert args[0] == ('', (('', (('', ('a', 'b')), 'c')), 'd'))
        assert args[1] == dangerous_string
        assert args[2] == ('', (1, ('', (2, 3))))


def test_no_input(capsys):
    """This test ensure that empty input do not lead the code to wait forever
    clingo to finish, since it will just wait for stdin input.

    So if this test takes time to run, you know why.

    Note the use of capsys fixture, allowing to disable the input patching
    that make it fail automatically, and therefore disturbing the functionality.

    """
    with capsys.disabled():
        assert tuple(clyngor.solve((), inline='')) == ()


@clingo_noncompliant
def test_syntax_error():
    assert not clyngor.have_clingo_module()
    with pytest.raises(clyngor.ASPSyntaxError) as excinfo:
        tuple(clyngor.solve((), inline='invalid', force_tempfile=True))
    assert excinfo.value.filename.startswith('/tmp/tmp')
    assert excinfo.value.lineno == 2
    assert excinfo.value.offset == 1
    assert excinfo.value.payload['char_end'] == 2
    assert excinfo.value.msg.startswith('unexpected EOF in file /tmp/tmp')
    assert excinfo.value.msg.endswith(' at line 2 and column 1-2')


@clingo_noncompliant
def test_syntax_error_semicolon():
    with pytest.raises(clyngor.ASPSyntaxError) as excinfo:
        tuple(clyngor.solve((), inline='color(X,red):- ;int(X,"adult").', force_tempfile=True))
    assert excinfo.value.filename.startswith('/tmp/tmp')
    assert excinfo.value.lineno == 1
    assert excinfo.value.offset == 16
    assert excinfo.value.msg.startswith('unexpected ; in file /tmp/tmp')
    assert excinfo.value.msg.endswith(' at line 1 and column 16-17')


@clingo_noncompliant
def test_syntax_error_brace():
    with pytest.raises(clyngor.ASPSyntaxError) as excinfo:
        tuple(clyngor.solve((), inline='color(X,red):- {{}}.', force_tempfile=True))
    assert excinfo.value.filename.startswith('/tmp/tmp')
    assert excinfo.value.lineno == 1
    assert excinfo.value.offset == 17
    assert excinfo.value.msg.startswith('unexpected { in file /tmp/tmp')
    assert excinfo.value.msg.endswith(' at line 1 and column 17-18')


@clingo_noncompliant
def test_syntax_error_brace_with_stdin():
    with pytest.raises(clyngor.ASPSyntaxError) as excinfo:
        tuple(clyngor.solve((), inline='color(X,red):- {{}}.'))
    assert excinfo.value.filename == '-'
    assert excinfo.value.lineno == 1
    assert excinfo.value.offset == 17
    assert excinfo.value.msg.startswith('unexpected { in file -')
    assert excinfo.value.msg.endswith(' at line 1 and column 17-18')


@clingo_noncompliant
def test_undefined_warning():
    assert not clyngor.have_clingo_module()
    with pytest.raises(clyngor.ASPWarning) as excinfo:
        tuple(clyngor.solve((), inline='b:- c.', error_on_warning=True, force_tempfile=True))
    assert excinfo.value.atom == 'c'
    assert len(excinfo.value.args) == 1
    start = "atom 'c' does not occur in any rule head in file /tmp/tmp"
    assert excinfo.value.args[0].startswith(start)
    assert excinfo.value.args[0].endswith(" at line 1 and column 5-6")

    # NB: the following should NOT raise any error (default value)
    tuple(clyngor.solve((), inline='b:- c.', error_on_warning=False))
    tuple(clyngor.solve((), inline='b:- c.'))
