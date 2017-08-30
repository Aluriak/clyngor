
import tempfile
from .test_api import asp_code  # fixture
from clyngor import ASP, utils


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
    as_dict_answers = tuple(ASP(asp_code).as_pyasp)
    fname = utils.save_answers_in_file(as_dict_answers)
    read_answers = frozenset(utils.load_answers_from_file(fname))

    # must be the same as regular repr of answer sets
    answers = frozenset(ASP(asp_code))
    assert answers == read_answers
