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
| clingo binary + clingo module | 168 passed, 9 skipped, 2 xfailed |
| clingo binary only | 156 passed, 22 skipped, 1 xfailed |
| clingo module only (no binary in PATH) | 141 passed, 36 skipped, 2 xfailed |

CI (`.github/workflows/tests.yml`) runs the three, across python
3.9/3.11/3.13, on every push and PR. The module-only job installs no
`gringo` package at all; locally, `PATH=/some/empty/dir` reproduces it.

The suite must also stay clean under `-W error::DeprecationWarning`:
that is what proves no code inside clyngor still reaches for the pre-1.0
global toggles.

## The two solving backends

clyngor can solve either by running the **clingo binary** as a subprocess
(parsing its stdout) or through the official **clingo python module** (API
objects). The two paths differ enough — statistics shape, embedded
`#script` support, propagator support, `time_limit`/`constants` support,
`is_unsatisfiable`/`is_unknown` — that all of them must be exercised.

Since 1.0, which one is used is carried by a `clyngor.Solver`
(`clyngor/solver.py`): a **frozen** dataclass of `(backend, binary_path)`,
validated at construction, derived with `.using(...)`. `backend='auto'`
prefers the binary and falls back to the module, so "module installed, no
binary" solves instead of raising.

Module-level entry points use `clyngor.default_solver()` when none is
given. That default is still process-wide state — `using_solver()` swaps
it for a block, `set_default_solver()` replaces it — but it is now one
validated object, and `solve(solver=...)` bypasses it entirely, which is
the only thread-safe way to pick a backend.

In tests:

- **Never** write a skip condition on `have_clingo_module()` or
  `have_python_support()`. Those read whichever backend the default solver
  resolves to at *collection* time, which is not the backend the test body
  runs in — and both are deprecated anyway. Use the helpers in
  `clyngor/test/definitions.py` (`clingo_module_importable()`,
  `binary_has_python_support()`, `module_has_python_support()`,
  `clingo_binary_available()`).
- A test that needs a specific backend says so with
  `run_with_clingo_binary_only` / `run_with_clingo_module_only`, which
  wrap the body in `using_solver()`. Five tests in `test_api.py` were
  silently relying on the binary until the module-only CI job appeared.
- An autouse fixture in `conftest.py` restores the default solver after
  every test, so a crashing test cannot leak its own into the next one.

## Gotchas worth remembering

- Since clingo 5.5, embedded `#script (python)` blocks are **opt-in** for
  module users; `Solver.module()` calls `clingo.script.enable_python()` so
  clyngor's documented `#script` support works in module mode. **Exactly
  once per process**: calling it on every module access segfaults the
  interpreter in a later, unrelated solving (drop the guard and the suite
  dies in `test_upapi`).
- The pip `clingo` package ships **no executable**, so "module installed,
  no binary" is a legitimate setup — since 1.0 it is a *solving* one, via
  the `auto` fallback. The probes in `utils.py` answer False rather than
  raising when no binary is around, while the `Solver` methods raise
  `SolverUnavailableError`: the probe is asking "is there support?", the
  method is being asked to use a solver that isn't there.
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

## Settled in 1.0 (don't reopen without reading these)

- **Global state → explicit config object.** Done: `clyngor.Solver`. The
  pre-1.0 toggles (`use_clingo_module`, `CLINGO_BIN_PATH`, …) still work
  on top of the default solver and emit `DeprecationWarning`, with a
  migration table in the README changelog. `CLINGO_BIN_PATH` assignment
  survives through a `ModuleType` subclass — a module cannot otherwise
  intercept an assignment to itself, and a silent no-op would be worse
  than the break.
- **Module-only fallback.** Done, as `backend='auto'`. It is *not*
  behavior-preserving, which is the whole reason it stayed open: the
  module path rejects `time_limit` and `constants`, reports statistics in
  clingo's nested shape, and fills neither `is_unsatisfiable` nor
  `is_unknown`. The CI job covers it.

## Open design questions (maintainer's call, not decided)

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
