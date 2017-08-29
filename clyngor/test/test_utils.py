
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
