"""Explicit, immutable description of how clyngor reaches clingo.

clingo can be reached in two very different ways: by running the **binary**
as a subprocess and parsing its output, or through the official **clingo
python module** and its API objects. Which one is used, and where the
binary lives, used to be module-level mutable state
(``clyngor.CLINGO_BIN_PATH``, ``clyngor.clingo_module``), flipped by
``use_clingo_module()``/``use_clingo_binary()``.

That state was never validated, was not thread-safe, and was read at
unpredictable times — a test could ask "is the module available?" while a
completely different mode was active. A ``Solver`` instead carries that
choice explicitly:

    >>> Solver(backend='module')
    Solver(backend='module', binary_path='clingo')

Instances are frozen: derive a new one with ``using()`` instead of
mutating.

    >>> Solver().using(binary_path='asprin')
    Solver(backend='auto', binary_path='asprin')

Invalid configurations are rejected at construction, not at solving time:

    >>> Solver(backend='moduel')
    Traceback (most recent call last):
      ...
    ValueError: backend must be one of 'auto', 'binary', 'module', not 'moduel'

"""

import re
import shutil
import subprocess
import importlib.util
from dataclasses import dataclass, replace


AUTO, BINARY, MODULE = 'auto', 'binary', 'module'
BACKENDS = (AUTO, BINARY, MODULE)
DEFAULT_BINARY_PATH = 'clingo'


# Enabling embedded python in the clingo module registers a handler in
# its C library; see Solver.module.
_python_enabled = False


class SolverUnavailableError(RuntimeError):
    """The backend a Solver asks for cannot be reached.

    Raised instead of letting a bare FileNotFoundError escape from the
    subprocess call, or a ModuleNotFoundError from the import.

    """


# Parsed out of `clingo --version --outf=2`. python and lua yield None
# when the binary was built without them.
_VERSION_FIELDS = {
    'address model': re.compile(r'Address model: ([3264]{2})-bit'),
    'clingo version': re.compile(r'clingo version ([0-9\.]+)'),
    'libgringo': re.compile(r'libgringo version ([0-9\.]+)'),
    'libclasp': re.compile(r'libclasp version ([0-9\.]+)'),
    'libpotassco': re.compile(r'libpotassco version ([0-9\.]+)'),
    'python': re.compile(r'with[out]{0,3}\sPython\s?([0-9\.]+)?'),
    'lua': re.compile(r'with[out]{0,3}\sLua\s?([0-9\.]+)?'),
}


@dataclass(frozen=True)
class Solver:
    """How to reach clingo: which backend, and where the binary is.

    backend -- 'binary', 'module', or 'auto' to pick whichever is there
    binary_path -- name or path of the clingo executable

    """

    backend: str = AUTO
    binary_path: str = DEFAULT_BINARY_PATH

    def __post_init__(self):
        if self.backend not in BACKENDS:
            raise ValueError(
                "backend must be one of {}, not {!r}"
                "".format(', '.join(map(repr, BACKENDS)), self.backend)
            )
        if not isinstance(self.binary_path, str) or not self.binary_path:
            raise ValueError(
                "binary_path must be a non-empty string, not {!r}"
                "".format(self.binary_path)
            )

    def using(self, **changes) -> 'Solver':
        """Return a copy of this solver, with given fields replaced.

        >>> Solver().using(backend='binary').backend
        'binary'

        """
        return replace(self, **changes)


    # What this solver can actually reach, in the current environment.

    @property
    def module_available(self) -> bool:
        """True if the official clingo module is importable.

        NB: a property of the environment only — unlike the historical
        ``have_clingo_module()``, it does not answer "is the module the
        active backend?".

        """
        return importlib.util.find_spec('clingo') is not None

    @property
    def binary_available(self) -> bool:
        "True if this solver's binary is reachable"
        return self.resolved_binary_path is not None

    @property
    def resolved_binary_path(self) -> str or None:
        "Absolute path of the clingo binary, or None if unreachable"
        return shutil.which(self.binary_path)

    @property
    def available(self) -> bool:
        "True if solving with this solver would find a backend"
        try:
            self.resolve()
        except SolverUnavailableError:
            return False
        return True

    def resolve(self) -> str:
        """Return the backend actually used: 'binary' or 'module'.

        With backend='auto', the binary comes first — it is the historical
        default, and it supports options ('time_limit', 'constants') the
        module path rejects. The module is the fallback for a deployment
        that pip-installed clingo but has no executable, which used to
        fail with a bare FileNotFoundError.

        Raises SolverUnavailableError when nothing can be reached.

        """
        if self.backend == BINARY:
            if self.binary_available:
                return BINARY
            raise SolverUnavailableError(
                "No clingo binary found at {!r}. Install one, pass a path "
                "with Solver(binary_path=...), or use the clingo module "
                "with Solver(backend='module').".format(self.binary_path)
            )
        if self.backend == MODULE:
            if self.module_available:
                return MODULE
            raise SolverUnavailableError(
                "The clingo module was asked for, but it is not importable. "
                "Install it with `pip install clingo`, or use a binary with "
                "Solver(backend='binary')."
            )
        if self.binary_available:
            return BINARY
        if self.module_available:
            return MODULE
        raise SolverUnavailableError(
            "Neither a clingo binary (looked for {!r}) nor the clingo "
            "module could be found. Install clingo, or clyngor-with-clingo "
            "which ships a binary.".format(self.binary_path)
        )

    @property
    def uses_module(self) -> bool:
        "True if solving would go through the clingo module"
        return self.available and self.resolve() == MODULE

    @property
    def uses_binary(self) -> bool:
        "True if solving would run the clingo binary"
        return self.available and self.resolve() == BINARY


    # Capabilities of the backend this solver resolves to.

    def version(self) -> dict:
        """Return clingo's version information, as a dict.

        The keys differ between backends: the binary reports everything
        `clingo --version` prints, the module only knows its own version
        and whether it runs embedded scripts.

        """
        if self.resolve() == MODULE:
            clingo = self.module()
            return {
                'clingo version': clingo.__version__,
                'python': '3' if self._module_runs_script('python') else None,
                'lua': 'yes' if self._module_runs_script('lua') else None,
            }
        process = subprocess.Popen(
            [self.binary_path, '--version', '--outf=2'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout = process.communicate()[0].decode()
        return {
            field: (match.groups()[0] if match else None)
            for field, match in (
                (field, regex.search(stdout))
                for field, regex in _VERSION_FIELDS.items()
            )
        }

    def has_python_support(self, py3: bool = True) -> bool:
        """True if this solver runs embedded #script (python) blocks.

        py3 -- ask for python 3 support (python 2 otherwise)

        """
        if self.resolve() == MODULE:
            return self._module_runs_script('python', py3=py3)
        version = self.version().get('python')  # None when built without
        if not version:
            return False
        return version[0] == ('3' if py3 else '2')

    def has_lua_support(self) -> bool:
        "True if this solver runs embedded #script (lua) blocks"
        if self.resolve() == MODULE:
            return self._module_runs_script('lua')
        return bool(self.version().get('lua'))

    def module(self):
        """Return the clingo module, ready to run embedded scripts.

        Since clingo 5.5, embedded #script (python) blocks are opt-in for
        module users, so enable them here — clyngor documents #script as
        supported.

        Exactly once per process. It registers a script handler in
        clingo's C library, so there is nothing to gain from doing it
        again, and something to lose: calling it on every access
        segfaults the interpreter later on, in an unrelated solving
        (reproducible by dropping the guard below and running the test
        suite, which then dies in test_upapi).

        """
        if not self.module_available:
            raise SolverUnavailableError(
                "The clingo module is not importable. Install it with "
                "`pip install clingo`."
            )
        import clingo
        global _python_enabled
        if not _python_enabled:
            _python_enabled = True
            try:
                from clingo.script import enable_python
            except ImportError:
                pass  # older module: scripts are always enabled
            else:
                enable_python()
        return clingo

    def _module_runs_script(self, language: str, py3: bool = True) -> bool:
        "True if the clingo module accepts an embedded script in *language*"
        if language == 'python':
            source = ("#script(python)\nimport sys\n"
                      "assert sys.version_info.major == {}\n#end.\n"
                      "".format('3' if py3 else '2'))
        else:
            source = "#script({}) #end.".format(language)
        control = self.module().Control()
        try:
            control.add("base", [], source)
        except RuntimeError:  # support not compiled in
            return False
        return True
