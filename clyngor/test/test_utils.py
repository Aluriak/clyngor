
import tempfile
from .test_api import asp_code  # fixture
from clyngor import solve, ASP, utils


def test_save_in_file(asp_code):
    answers = frozenset(ASP(asp_code))
    with tempfile.NamedTemporaryFile('w', delete=False) as ofd:
        ofd.write('\n'.join(utils.answer_set_to_str(answer) for answer in answers))
        fname = ofd.name

    with open(fname) as ifd:
        read_answers = frozenset(
            frozenset(utils.answer_set_from_str(line))
            for line in ifd
        )

    assert read_answers == answers


def test_file_saving_api(asp_code):
    answers = frozenset(ASP(asp_code))
    fname = utils.save_answers_in_file(answers)
    read_answers = frozenset(utils.load_answers_from_file(fname))
    assert answers == read_answers


def test_file_saving_api_with_dict(asp_code):
    # create the read_answers from the dictionary repr of answer sets
    as_dict_answers = tuple(ASP(asp_code).by_predicate)
    fname = utils.save_answers_in_file(as_dict_answers)
    read_answers = frozenset(utils.load_answers_from_file(fname))

    # must be the same as regular repr of answer sets
    answers = frozenset(ASP(asp_code))
    assert answers == read_answers


def test_file_saving_api_with_as_pyasp(asp_code):
    # create the read_answers from the dictionary repr of answer sets
    as_pyasp_answers = tuple(ASP(asp_code).as_pyasp)
    fname = utils.save_answers_in_file(as_pyasp_answers)
    read_answers = frozenset(utils.load_answers_from_file(fname))

    # must be the same as regular repr of answer sets
    answers = frozenset(ASP(asp_code))
    assert answers == read_answers


def test_remove_quotes_argument():
    example_inputs = ['"\"a\"","b\""', '\\"a\\","b\\"']
    expected_results = ['"a",b"', '\\"a\\","b\\"']

    for found, expected in zip(map(utils.remove_arguments_quotes,example_inputs), expected_results):
        assert found == expected

def test_answer_set_to_str():
    generate_answer_set_as_str = utils.generate_answer_set_as_str
    assert '.'.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ())))) == 'a(1,2).b'
    assert ''.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ())), atom_end='.')) == 'a(1,2).b.'
    assert '1'.join(generate_answer_set_as_str((('a', (1, 2)), ('b', ())), atom_end='2')) == 'a(1,2)21b2'
    assert ' '.join(generate_answer_set_as_str((('', ('v', 2)), ('b', (('', ['v', 3]),))), atom_end='.')) == '(v,2). b((v,3)).'
    assert ' '.join(generate_answer_set_as_str((('', ('', ('', (2,)))),))) == '("",(2,))'
    assert '.'.join(generate_answer_set_as_str((('a', (('', ('1', '2')),)),))) == 'a((1,2))'

def test_answer_set_to_str_with_tuple():
    asp = 'a(b,(2,3,(a,b))).'
    model = next(ASP(asp).parse_args)
    assert ' '.join(utils.generate_answer_set_as_str(model, atom_end='.')) == asp

def test_answer_set_to_str_complex():
    asp = 'a(a(2,3),(2,),b(c((d,),(e,f)))).'
    models = tuple(ASP(asp).parse_args)
    print('CAREFUL:', models)
    answerset = models[0]
    models = tuple(ASP(asp))
    print('NORMAL :', models)
    assert ' '.join(utils.generate_answer_set_as_str(answerset, atom_end='.')) == asp

def test_with_opts():
    ASP = r"""
1 { a; b }.
#minimize { 2,t:a; 2,t:b; 1,u:b; 2,v:b }.
    """
    answer = solve(inline=ASP, options='--opt-mode=optN')
    found = list(utils.opt_models_from_clyngor_answers(answer))
    assert found == [frozenset({('a', ())})]
