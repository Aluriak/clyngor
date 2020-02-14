
import pytest
import clyngor
from clyngor.answers import Answers
from clyngor.as_pyasp import Atom, TermSet

@pytest.fixture
def simple_answers():
    return Answers((
        'a(0) b(1)',
        'c(2) d(3)',
        'e(4) f(5)',
        'g(6) h(7)',
        'i j',
    ))

@pytest.fixture
def quotes_answers():
    return Answers((
        'a("c") b("d","e")',
        'a("c") b("d","e")',
        'a("c") b("d","e")',
        'a("c") b("d","e")',
        'a("c") b("d","e")',
    ))

@pytest.fixture
def complex_quotes_answers():
    return Answers((
        'a("\\"cou\\"cou\\"") b("\\"&\\"&\\"1234\\"\\"&\\"")',  # Random gibberish
    ))

@pytest.fixture
def multiple_args():
    return Answers((
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
        'edge(4,"s…lp.") r_e_l(1,2)',
    ))

@pytest.fixture
def noarg_answers():
    return Answers((
        '',
        'a',
        'b c',
        'd e f',
    ))

@pytest.fixture
def many_atoms_answers():
    return Answers((
        'a b(4) b(3) a(1) vv(1) vv v(a) v(b)',
    ))

@pytest.fixture
def default_negation_answers():
    return Answers((
        'ok -ko',
        '-occurs(apply(drychem,fire_in(bin)), 2) ok -ko',
    ))

@pytest.fixture
def optimized_answers():
    return Answers((
        ('edge(4,"s…lp.") r_e_l(1,2)', 1, False, 1),
        ('edge(4,"s…lp.") r_e_l(1,2)', 1, False, 2),
        ('edge(4,"s…lp.") r_e_l(1,2)', 2, False, 3),
        ('edge(4,"s…lp.") r_e_l(1,2)', 3, False, 4),
        ('edge(4,"s…lp.") r_e_l(1,2)', 4, False, 5),
    ), with_optimization=True)


def test_parsing_args_when_noargs(noarg_answers):
    answers = noarg_answers
    assert next(answers) == frozenset()
    assert next(answers) == {('a', ())}
    answers = noarg_answers.parse_args
    assert next(answers) == {('b', ()), ('c', ())}
    answers.by_predicate
    assert next(answers) == {'d': frozenset({()}), 'e': frozenset({()}),
                             'f': frozenset({()})}

def test_discard_quotes(quotes_answers):
    answers = quotes_answers
    assert next(answers) == {('a', ('"c"',)), ('b', ('"d"','"e"',))}
    answers = quotes_answers.discard_quotes
    assert next(answers) == {('a', ('c',)), ('b', ('d','e',))}
    answers = quotes_answers.discard_quotes.by_predicate
    assert next(answers) == {'a': frozenset({('c',)}), 'b': frozenset({('d', 'e')})}
    answers = quotes_answers.discard_quotes.by_predicate.first_arg_only
    assert next(answers) == {'a': frozenset({'c'}), 'b': frozenset({'d'})}
    answers = quotes_answers.discard_quotes.by_predicate.first_arg_only.atoms_as_string
    assert next(answers) == {'a("c")', 'b("d")'}
    assert next(answers, None) is None

def test_discard_quotes_careful_parsing(quotes_answers):
    answers = quotes_answers.careful_parsing
    assert next(answers) == {('a', ('"c"',)), ('b', ('"d"','"e"',))}
    answers = quotes_answers.careful_parsing.discard_quotes
    assert next(answers) == {('a', ('c',)), ('b', ('d','e',))}
    answers = quotes_answers.careful_parsing.discard_quotes.by_predicate
    assert next(answers) == {'a': frozenset({('c',)}), 'b': frozenset({('d', 'e')})}
    answers = quotes_answers.discard_quotes.by_predicate.first_arg_only
    assert next(answers) == {'a': frozenset({'c'}), 'b': frozenset({'d'})}
    answers = quotes_answers.careful_parsing.discard_quotes.by_predicate.first_arg_only.atoms_as_string
    assert next(answers) == {'a("c")', 'b("d")'}
    assert next(answers, None) is None


def test_discard_quotes_complex(complex_quotes_answers):
    answers = complex_quotes_answers.discard_quotes
    assert next(answers) == {('a', (r'\"cou\"cou\"',)), ('b', (r'\"&\"&\"1234\"\"&\"',))}
    assert next(answers, None) is None

def test_discard_quotes_complex_careful_parsing(complex_quotes_answers):
    answers = complex_quotes_answers.discard_quotes.careful_parsing
    assert next(answers) == {('a', (r'\"cou\"cou\"',)), ('b', (r'\"&\"&\"1234\"\"&\"',))}
    assert next(answers, None) is None


def test_as_pyasp_atom():
    answers = Answers(('a("b","d")',)).as_pyasp
    for atom in next(answers):
        assert atom == Atom(predicate='a', args=('"b"','"d"'))
        print(atom)
    answers = Answers(('a(1,"2.3")',)).as_pyasp
    for atom in next(answers):
        assert atom == Atom(predicate='a', args=(1,'"2.3"'))
        print(atom)

def test_bug_issue_7():
    "inconsistencies in parsing when clingo module is used"
    models = clyngor.solve(inline='a(1). e(X):- a(X).', use_clingo_module=True).sorted.atoms_as_string
    model = next(models)
    assert model == ('a(1)', 'e(1)')
    with pytest.raises(StopIteration):
        next(models)  # only one model
    # assert False, 'everything ok'

def test_as_pyasp_termset_frozenset():
    answers = Answers(('a("b","d")',)).as_pyasp
    assert next(answers) == frozenset((Atom(predicate='a',args=('"b"','"d"')),))

def test_as_pyasp_termset_frozenset_union():
    answers = Answers(('a("b","d")',)).as_pyasp
    answer_a = next(answers)
    expected_a = frozenset((Atom(predicate='a',args=('"b"','"d"')),))
    assert answer_a == expected_a
    assert next(answers, None) is None
    answers = Answers(('b("b","d")',)).as_pyasp
    answer_b = next(answers)
    expected_b = frozenset((Atom(predicate='b',args=('"b"','"d"')),))
    assert answer_b == expected_b
    assert next(answers, None) is None
    assert isinstance(answer_a, TermSet)
    assert isinstance(answer_b, TermSet)
    assert answer_a.union(answer_b) == frozenset((Atom(predicate='a',args=('"b"','"d"')), Atom(predicate='b',args=('"b"','"d"'))))
    # no modification of objects
    assert answer_a == expected_a
    assert answer_b == expected_b

def test_as_pyasp_termset_add():
    answers = Answers(('a("b","d")',)).as_pyasp
    answer_a = next(answers)
    expected_a = frozenset((Atom(predicate='a',args=('"b"','"d"')),))
    assert answer_a == expected_a
    assert next(answers, None) is None
    answer_a.add(Atom(predicate='b',args=('"b"','"d"')))
    expected_a = frozenset((Atom(predicate='a',args=('"b"','"d"')), Atom(predicate='b',args=('"b"','"d"'))))
    assert answer_a == expected_a

def test_as_pyasp_termset_termset():
    answers = Answers(('a("b","d")',)).as_pyasp
    assert next(answers) == TermSet((Atom(predicate='a',args=('"b"','"d"')),))

def test_as_pyasp_termset_string():
    answers = Answers(('a("b","d")',)).as_pyasp
    assert str(next(answers)) == 'a("b","d").'

def test_as_pyasp_termset_termset_by_predicate():
    answers = Answers(('a("b","d")',)).as_pyasp.by_predicate
    assert next(answers) == {'a': TermSet((Atom(predicate='a',args=('"b"','"d"')),))}

def test_discard_quotes_with_as_pyasp_termset():
    answers = Answers(('a("b","d")',)).as_pyasp.discard_quotes
    assert next(answers) == TermSet((Atom(predicate='a',args=('b','d')),))

def test_discard_quotes_with_as_pyasp_termset_and_careful_parsing():
    answers = Answers(('a("b","d")',)).parse_args.as_pyasp.discard_quotes.careful_parsing
    assert next(answers) == TermSet((Atom(predicate='a',args=('b','d')),))


def test_multiple_tunning_no_arg(noarg_answers):
    answers = noarg_answers.no_arg
    assert next(answers) == frozenset()
    assert next(answers) == {'a'}
    assert next(answers) == {'b', 'c'}
    answers.by_predicate
    assert next(answers) == {'d': frozenset(), 'e': frozenset(), 'f': frozenset()}


def test_by_predicate_and_arity(simple_answers):
    answers = simple_answers.by_predicate
    assert next(answers) == {'a': {(0,)}, 'b': {(1,)}}
    answers.by_arity
    assert next(answers) == {'c': {(2,)}, 'd': {(3,)}, ('c', 1): {(2,)}, ('d', 1): {(3,)}, 'c/1': {(2,)}, 'd/1': {(3,)}}
    assert len(next(answers)) == 6
    assert len(next(answers)) == 6
    assert len(next(answers)) == 6
    assert next(answers, None) is None


def test_multiple_tunning(simple_answers):
    answers = simple_answers
    assert next(answers) == {('a', (0,)), ('b', (1,))}
    answers.by_predicate
    assert next(answers) == {'c': {(2,)}, 'd': {(3,)}}
    answers.first_arg_only
    assert next(answers) == {'e': {4}, 'f': {5}}
    answers.int_not_parsed
    assert next(answers) == {'g': {'6'}, 'h': {'7'}}
    assert next(answers) == {'i': {()}, 'j': {()}}
    assert next(answers, None) is None


def test_tunning_first_arg_only(simple_answers):
    answers = simple_answers
    answers.first_arg_only
    assert next(answers) == {('a', 0), ('b', 1)}
    assert next(answers) == {('c', 2), ('d', 3)}
    assert next(answers) == {('e', 4), ('f', 5)}
    assert next(answers) == {('g', 6), ('h', 7)}
    assert next(answers) == {('i', ()), ('j', ())}
    assert next(answers, None) is None


def test_tunning_atoms_as_string_and_sorted_more_complex(many_atoms_answers):
    answers = many_atoms_answers.atoms_as_string.sorted.first_arg_only
    assert next(answers) == tuple(sorted('a b(4) b(3) a(1) vv(1) vv v(a) v(b)'.split()))
    assert next(answers, None) is None


def test_tunning_atoms_as_string_and_sorted_more_complex_careful_parsing(many_atoms_answers):
    answers = many_atoms_answers.atoms_as_string.sorted.first_arg_only.careful_parsing
    assert next(answers) == tuple(sorted('a b(4) b(3) a(1) vv(1) vv v(a) v(b)'.split()))
    assert next(answers, None) is None


def test_default_negation(default_negation_answers):
    answers = default_negation_answers
    assert next(answers) == {('ok', ()), ('-ko', ())}
    assert next(answers) == {('-occurs', ('apply(drychem,fire_in(bin))', 2)), ('ok', ()), ('-ko', ())}
    assert next(answers, None) is None


def test_first_arg_only():
    answers = Answers(('p(1,2,3)',)).first_arg_only
    assert next(answers) == {('p', 1)}


def test_first_arg_only_with_careful_parsing():
    answers = Answers(('p("1,5","2,456",3)',)).first_arg_only.careful_parsing
    assert next(answers) == {('p', '"1,5"')}


def test_tunning_atoms_as_string_and_sorted(simple_answers):
    answers = simple_answers.atoms_as_string.sorted
    assert next(answers) == ('a(0)', 'b(1)')
    assert next(answers) == ('c(2)', 'd(3)')
    assert next(answers) == ('e(4)', 'f(5)')
    assert next(answers) == ('g(6)', 'h(7)')
    assert next(answers) == ('i', 'j')
    assert next(answers, None) is None


def test_tunning_atoms_as_string(simple_answers):
    answers = simple_answers
    answers.atoms_as_string
    assert next(answers) == {'a(0)', 'b(1)'}
    assert next(answers) == {'c(2)', 'd(3)'}
    answers.careful_parsing
    assert next(answers) == {'e(4)', 'f(5)'}
    assert next(answers) == {'g(6)', 'h(7)'}
    assert next(answers) == {'i', 'j'}
    assert next(answers, None) is None


def test_multiple_args_in_atoms(multiple_args):
    answers = multiple_args
    assert next(answers) == {('edge', (4, '"s…lp."')), ('r_e_l', (1, 2))}
    answers = multiple_args.discard_quotes
    assert next(answers) == {('edge', (4, 's…lp.')), ('r_e_l', (1, 2))}
    answers = answers.atoms_as_string
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    answers.careful_parsing
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    assert next(answers) == {'edge(4,"s…lp.")', 'r_e_l(1,2)'}
    assert next(answers, None) is None


def test_optimization_access(optimized_answers):
    answers = optimized_answers.with_optimization
    assert next(answers) == ({('edge', (4, '"s…lp."')), ('r_e_l', (1, 2))}, 1)
    answers = optimized_answers.with_optimization.discard_quotes
    assert next(answers) == ({('edge', (4, 's…lp.')), ('r_e_l', (1, 2))}, 1)
    answers = answers.no_arg
    assert next(answers) == ({'edge', 'r_e_l'}, 2)
    answers.atoms_as_string.with_optimality
    assert next(answers) == ({'edge(4,"s…lp.")', 'r_e_l(1,2)'}, 3, False)
    answers.with_answer_number
    assert next(answers) == ({'edge(4,"s…lp.")', 'r_e_l(1,2)'}, 4, False, 5)
    assert next(answers, None) is None

def test_int_not_parsed():
    "Ensures that .int_not_parsed modifier behave correctly"
    asp = 'a(1). #show a/1.'
    for model in next(clyngor.ASP(asp)):
        t = type(model[1][0])
        assert t is int, t
    for model in next(clyngor.ASP(asp).int_not_parsed):
        t = type(model[1][0])
        assert t is str, t

def test_atoms_with_leading_underscore():
    """needed to test leading underscores in naive parsing ;
    next test will fall under the case where careful parsing is automatically activated"""
    get_answers = lambda: Answers(('_a(_b,_c,d) _e',)).parse_args
    # naive parsing
    answers = get_answers()
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((('_a', ('_b', '_c', 'd')), ('_e', ())))
    assert answer_a == expected_a, (answer_a, type(answer_a))
    # careful parsing
    answers = get_answers().careful_parsing
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((('_a', ('_b', '_c', 'd')), ('_e', ())))
    assert answer_a == expected_a, answer_a

def test_atoms_with_leading_underscore_with_nested():
    get_answers = lambda: Answers(('_a("b",_b(c,_d)) _c',)).parse_args
    # naive parsing (NB: careful parsing should be automatically activated)
    answers = get_answers()
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((('_a', ('"b"', ('_b', ('c', '_d')))), ('_c', ())))
    assert answer_a == expected_a, (answer_a, type(answer_a))
    # careful parsing
    answers = get_answers().careful_parsing
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((('_a', ('"b"', ('_b', ('c', '_d')))), ('_c', ())))
    assert answer_a == expected_a, answer_a

def test_pyasp_and_nested_atoms():
    get_answers = lambda: Answers(('a(b(c,d))',)).parse_args
    # without as_pyasp
    answers = get_answers()
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((('a', (('b', ('c', 'd')),)),))
    assert answer_a == expected_a, (answer_a, type(answer_a))
    # with as_pyasp
    answers = get_answers().as_pyasp
    answer_a = next(answers)
    assert next(answers, None) is None, "there is more than one model"
    expected_a = frozenset((Atom('a', (Atom('b', ('c', 'd')),)),))
    print('LBTL:', type(answer_a), answer_a)
    assert answer_a == expected_a, (answer_a, type(answer_a))
