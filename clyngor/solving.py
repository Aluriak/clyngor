"""Low level interface to clingo.

"""


import re
import tempfile
import subprocess
import clyngor


REG_ANSWER = re.compile(r'Answer: ([0-9]+)')
REG_ANSWER_SET = re.compile(r'([a-z][a-zA-Z0-9_]*)\(([^)]+)\)')


def solve(files:iter, options:iter=[], nb_model:int=0,
          subproc_shell:bool=False, print_command:bool=False,
          inline_source:str=None) -> iter:
    """Run the solver on given files, with given options, and yield
    answers found.

    files -- iterable of files feeding the solver
    options -- string or iterable of options for clingo
    subproc_shell -- use shell=True in subprocess call (NB: you should not)
    print_command -- print full command to stdout before running it
    inline_source -- ASP source code to feed the solver with

    Shortcut to clingo's options:
    nb_model -- number of model to output (0 for all (default))

    Yield answers.
    TODO: return stderr.

    """
    if isinstance(files, str):
        files = [files]
    if isinstance(options, str):
        options = [options]
    if inline_source:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as fd:
            fd.write(inline_source)
            files = (*files, fd.name)

    command = [clyngor.CLINGO_BIN_PATH, *options, *files, '-n ' + str(nb_model)]
    if print_command:
        print(command)
    clingo = subprocess.Popen(
        command,
        stderr = subprocess.PIPE,
        stdout = subprocess.PIPE,
        shell=bool(subproc_shell),
    )

    for line in clingo.stdout:
        line = line.decode().strip()
        if line.startswith(('Answer: ', 'Time')):
            pass
        else:  # other line are maybe answers
            current_answer = set()
            for match in REG_ANSWER_SET.finditer(line):
                pred, args = match.groups(0)
                current_answer.add((pred, tuple(args.split(','))))
            if current_answer:
                yield current_answer


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
