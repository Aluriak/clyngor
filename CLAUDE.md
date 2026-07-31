# clyngor — notes for Claude Code

Python wrapper around the clingo ASP solver.

## Running the tests

```
python -m pytest clyngor --doctest-modules -rs      # what the CI runs
make t                                              # same, via the Makefile
python -m pytest clyngor --doctest-modules --quick  # skip the slow ones
```

`--doctest-modules` matters: part of the documented behavior lives in
docstrings. `-rs` matters too — *which* tests skip is the quickest read on
what the current environment supports.

Expected results, depending on the environment:

| environment | result |
|---|---|
| clingo binary + clingo module | 130 passed, 6 skipped, 2 xfailed |
| clingo binary only | 122 passed, 15 skipped, 1 xfailed |

CI (`.github/workflows/tests.yml`) runs both, across python 3.9/3.11/3.13,
on every push and PR.

## The two solving backends

clyngor can solve either by running the **clingo binary** as a subprocess
(parsing its stdout) or through the official **clingo python module** (API
objects). The two paths differ enough — statistics shape, embedded
`#script` support, propagator support — that both must be exercised.

Which one is active is **mutable global state** (`clyngor.use_clingo_binary()`
/ `use_clingo_module()`), and clyngor starts in *binary* mode even when the
module is installed.

That global state is a recurring source of bugs. In particular, in tests:

- **Never** write a skip condition on `have_clingo_module()` or
  `have_python_support()`. Those read whichever mode happens to be active
  at *collection* time, which is not the mode the test body runs in. Use
  the mode-specific helpers in `clyngor/test/definitions.py`
  (`clingo_module_importable()`, `binary_has_python_support()`,
  `module_has_python_support()`, `clingo_binary_available()`).
- An autouse fixture in `conftest.py` restores the global state after every
  test, so a crashing test cannot leak its mode into the next one.

## Gotchas worth remembering

- Since clingo 5.5, embedded `#script (python)` blocks are **opt-in** for
  module users; `load_clingo_module()` calls `clingo.script.enable_python()`
  so clyngor's documented `#script` support works in module mode.
- The pip `clingo` package ships **no executable**, so "module installed,
  no binary" is a legitimate setup. Binary probes answer False rather than
  raising, and binary-dependent tests skip.
- Modern clingo *binaries* have no python support (ubuntu's `gringo`
  package included), which is why `upapi` is tested through the module.
  The three propagator tests using embedded scripts still skip everywhere.
- `clyngor-parser/` is a **separate sibling project**, not packaged with
  clyngor (`packages = clyngor`). It is the only thing using pyPEG2 — which
  used to be a hard install dependency of clyngor and broke `pip install`
  entirely, since pyPEG2 no longer builds. Don't reintroduce it.

## Contract tests

`clyngor/test/test_known_issues.py` pins the current behavior of open
issues, with **strict xfails** that fail loudly once an issue is fixed —
they are the signal to update the test alongside the fix.

- **#5**: `solve()` does not wait for the clingo subprocess; side effects of
  embedded scripts are only guaranteed after consuming the answers.
- **#19**: `careful_parsing_required()` decisions, and its known false
  negative (a closing paren inside quotes escapes detection, so the naive
  parser silently garbles the input) — strict xfail.
- **#23**: statistics are a flat str→str dict in binary mode and clingo's
  nested dicts in module mode — strict xfail on their divergence, to be
  flipped when a common structure is chosen.

## Open design questions (maintainer's call, not decided)

- **Module-only fallback.** With the module installed but no binary,
  clyngor still defaults to binary mode and fails with `FileNotFoundError`.
  Should it fall back to the module? Note module mode has its own
  restrictions (`time_limit` and `constants` raise `ValueError`), so the
  fallback is not behavior-preserving. No CI config covers this case.
- **Global state → explicit config object.** The mutable module-level state
  (`clingo_module`, `CLINGO_BIN_PATH`) is not thread-safe, is validated
  nowhere, and is the common root of issues #28/#30 and of the test-suite
  bugs above. Replacing it with an explicit `Solver`/context object would
  remove a whole class of bugs, at the cost of an API break.
- **`Answers` flags → composable pipeline.** `Answers` carries ~12 boolean
  flags whose combinations are resolved by cascading `if/elif` in
  `_parse_answer`/`_format`, which makes every new option risky. A design
  was sketched: three named extension points (parsing strategy, atom
  encoder, collection builder) instead of a bag of booleans, keeping the
  chained public API (`.by_predicate.as_pyasp.sorted`) unchanged. NB
  `as_pyasp` + `by_predicate` are *not* independent, so the collection
  builder must take the atom encoder as a parameter.
- **Two parsers (#19).** A naive regex parser and an Arpeggio one coexist,
  chosen by heuristic. Is the naive one still worth its dead weight, or can
  a single correct parser replace both?
