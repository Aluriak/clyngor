"""Contract tests attached to open issues.

These tests pin the *current* behavior related to open issues of clyngor,
so that (1) the behavior under discussion is documented and reproducible,
and (2) fixing the issue makes the corresponding xfail tests fail loudly
(strict=True), signalling that they must be updated alongside the fix.

- issue #5: solve() does not wait for the underlying clingo subprocess.
- issue #19: naive vs careful parser agreement, and the autodetection
  implemented by parsing.careful_parsing_required().
- issue #23: statistics have entirely different shapes in binary mode
  and in module mode.

"""
import os
import time
import tempfile

import pytest
import clyngor
from clyngor import solve, parsing
from clyngor.answers import naive_parsing_of_answer_set
from clyngor.parsing import careful_parsing_required
from .definitions import run_with_clingo_binary_only, run_with_clingo_module_only


# ISSUE #5 #################################################################

@run_with_clingo_binary_only
def test_solve_does_not_wait_for_subprocess():
    """Contract of issue #5: in binary mode, solve() spawns clingo and
    returns immediately; side effects of embedded scripts are only
    guaranteed to be visible once the answers have been fully consumed.

    Reproduces the issue's scenario with an embedded script writing a
    file (in lua, since modern clingo binaries lack python support).

    """
    if not clyngor.have_lua_support():
        pytest.skip('clingo binary has no lua support')
    with tempfile.TemporaryDirectory() as tmpdir:
        result_file = os.path.join(tmpdir, 'result.txt')
        encoding = os.path.join(tmpdir, 'encoding.lp')
        with open(encoding, 'w') as fd:
            fd.write("""
            #script (lua)
            function main(prg)
                prg:ground({{"base", {}}})
                prg:solve()
                os.execute("sleep 1")
                local f = io.open(\"""" + result_file + """\", "w")
                f:write("done.")
                f:close()
            end
            #end.
            a.
            """)

        start = time.time()
        answers = solve(encoding)
        assert time.time() - start < 0.9, "solve() blocked until subprocess end"
        assert not os.path.exists(result_file), \
            "the embedded script ended before solve() returned"

        tuple(answers)  # consuming the answers waits for clingo's output to end
        for _ in range(50):  # be nice with slow machines
            if os.path.exists(result_file):
                break
            time.sleep(0.1)
        assert os.path.exists(result_file)


# ISSUE #19 ################################################################

# (input line, careful parsing needed, naive parser correct on it)
PARSING_CASES = (
    ('a b c', False, True),
    ('a(1) b(2,3)', False, True),
    ('a("hello world")', False, True),
    ('a(b(1))', True, False),
    ('a("text, with (parens)")', True, False),
    ('a("(")', True, True),
)


@pytest.mark.parametrize('line,careful_needed,_', PARSING_CASES)
def test_careful_parsing_detection(line, careful_needed, _):
    """careful_parsing_required() must flag every input the naive parser
    would garble (false positives are only a performance concern)."""
    assert careful_parsing_required(line) == careful_needed


@pytest.mark.parametrize(
    'line', [case for case, careful_needed, _ in PARSING_CASES if not careful_needed])
def test_parsers_agree_when_careful_not_required(line):
    """Whenever autodetection keeps the naive parser, both parsers must
    agree: this is what makes the autodetection of issue #19 sound."""
    naive = frozenset(naive_parsing_of_answer_set(line))
    careful = frozenset(parsing.Parser().parse_terms(line))
    assert naive == careful


@pytest.mark.parametrize(
    'line', [case for case, _, naive_ok in PARSING_CASES if not naive_ok])
def test_naive_parser_known_limitations(line):
    """The naive parser garbles these inputs: this is why the
    autodetection matters. If this test starts failing, the naive parser
    handles them now, and issue #19 may be reconsidered."""
    naive = frozenset(naive_parsing_of_answer_set(line))
    careful = frozenset(parsing.Parser().parse_terms(line))
    assert naive != careful


@pytest.mark.xfail(reason="issue #19: careful_parsing_required() misses "
                          "a closing paren inside quotes, so the naive "
                          "parser silently garbles this input",
                   strict=True)
def test_careful_parsing_detection_quoted_closing_paren():
    line = 'a("b)c")'
    assert careful_parsing_required(line), \
        "input garbled by the naive parser must be flagged"


# ISSUE #23 ################################################################

@run_with_clingo_binary_only
def test_statistics_shape_binary():
    """In binary mode, statistics are a flat str-to-str dict parsed from
    clingo's stdout."""
    answers = solve((), inline='a.', force_tempfile=True)
    tuple(answers)
    stats = answers.statistics
    assert isinstance(stats, dict)
    assert {'Models', 'Calls', 'Time', 'CPU Time'} <= set(stats)
    assert all(isinstance(k, str) and isinstance(v, str)
               for k, v in stats.items())


@run_with_clingo_module_only
def test_statistics_shape_module():
    """In module mode, statistics are clingo's own nested float dicts."""
    answers = solve((), inline='a.', force_tempfile=True)
    tuple(answers)
    stats = answers.statistics
    assert isinstance(stats, dict)
    assert {'problem', 'solving', 'summary'} <= set(stats)


@run_with_clingo_module_only
@pytest.mark.xfail(reason="issue #23: statistics have entirely different "
                          "shapes in binary mode and in module mode; a "
                          "common data structure is yet to be chosen",
                   strict=True)
def test_statistics_shapes_agree():
    answers = solve((), inline='a.', force_tempfile=True, use_clingo_module=False)
    tuple(answers)
    binary_keys = set(answers.statistics)

    answers = solve((), inline='a.', force_tempfile=True)
    tuple(answers)
    module_keys = set(answers.statistics)

    assert binary_keys == module_keys
