"""Low level interface to clingo.

"""


import re
import shlex
import tempfile
import subprocess
import clyngor
from clyngor.answers import Answers
from clyngor.utils import cleaned_path


def solve(files:iter=(), options:iter=[], inline:str=None,
          subproc_shell:bool=False, print_command:bool=False,
          nb_model:int=0, time_limit:int=0, constants:dict={},
          clean_path:bool=True) -> iter:
    """Run the solver on given files, with given options, and return
    an Answers instance yielding answer sets.

    files -- iterable of files feeding the solver
    options -- string or iterable of options for clingo
    inline -- ASP source code to feed the solver with
    subproc_shell -- use shell=True in subprocess call (NB: you should not)
    print_command -- print full command to stdout before running it
    clean_path -- clean the path of given files before using them

    Shortcut to clingo's options:
    nb_model -- number of model to output (0 for all (default))
    time_limit -- zero or number of seconds to wait before interrupting solving
    constants -- mapping name -> value of constants for the grounding

    """
    files = [files] if isinstance(files, str) else files
    files = tuple(map(cleaned_path, files) if clean_path else files)
    run_command = command(files, options, inline, nb_model, time_limit, constants)
    if print_command:
        print(run_command)

    clingo = subprocess.Popen(
        run_command,
        stderr = subprocess.PIPE,
        stdout = subprocess.PIPE,
        shell=bool(subproc_shell),
    )

    def gen_answers():
        stdout = iter(clingo.stdout)
        while True:
            cur_line = next(stdout).decode()
            if cur_line.startswith('Answer: '):
                yield next(stdout).decode()

    return Answers(gen_answers(), command=' '.join(run_command))


def command(files:iter=(), options:iter=[], inline:str=None,
            nb_model:int=0, time_limit:int=0, constants:dict={}) -> iter:
    """Return the shell command running the solver on given files,
    with given options.

    files -- iterable of files feeding the solver
    options -- string or iterable of options for clingo
    inline -- ASP source code to feed the solver with

    Shortcut to clingo's options:
    nb_model -- number of model to output (0 for all (default))
    time_limit -- zero or number of seconds to wait before interrupting solving
    constants -- mapping name -> value of constants for the grounding

    """
    files = [files] if isinstance(files, str) else list(files)
    options = list(shlex.split(options) if isinstance(options, str) else options)
    if inline:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as fd:
            fd.write(inline)
            files = tuple(files) + (fd.name,)
    if constants:
        for name, value in constants.items():
            options.append('-c {}={}'.format(name,value))
    if time_limit:
        try:
            time_limit = int(time_limit)
        except ValueError:
            raise ValueError("Time limit should be integer, not " + type(time_limit).__name__)
        options.append('--time-limit=' + str(time_limit))
    if nb_model:
        try:
            nb_model = int(nb_model)
        except ValueError:
            raise ValueError("Number of model must be int, not " + type(nb_model).__name__)
        if nb_model < 0:
            raise ValueError("Number of model must be >= 0.")
    else:
        nb_model = 0

    return [clyngor.CLINGO_BIN_PATH, *options, *files, '-n ' + str(nb_model)]


def clingo_version() -> dict:
    """Return clingo's version information in a dict"""
    clingo = subprocess.Popen(
        [clyngor.CLINGO_BIN_PATH, '--version', '--outf=2'],
        stderr = subprocess.PIPE,
        stdout = subprocess.PIPE,
    )
    fields = {
        'address model': re.compile(r'Address model: ([3264]{2})-bit'),
        'clingo version': re.compile(r'clingo version ([0-9\.]+)'),
        'libgringo': re.compile(r'libgringo version ([0-9\.]+)'),
        'libclasp': re.compile(r'libclasp version ([0-9\.]+)'),
        'libpotassco': re.compile(r'libpotassco version ([0-9\.]+)'),
        'python': re.compile(r'with[out]{0,3}\sPython\s?([0-9\.]+)?'),
        'lua': re.compile(r'with[out]{0,3}\sLua\s?([0-9\.]+)?'),
    }
    stdout = clingo.communicate()[0].decode()

    return {
        field: reg.search(stdout).groups()[0]
        for field, reg in fields.items()
    }
