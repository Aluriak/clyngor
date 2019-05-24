"""Implementation of decoupled grounding/solving interface"""

from clyngor import solve


def solve_from_grounded(grounded_program:str, **kwargs_to_solver):
    if 'options' not in kwargs_to_solver:
        kwargs_to_solver['options'] = ''
    kwargs_to_solver['options'] += ' --mode=clasp'
    if 'inline' in kwargs_to_solver:
        print('WARNING inline argument was passed to solve_from_grounded. It will be ignored.')
    kwargs_to_solver['inline'] = grounded_program
    return solve(**kwargs_to_solver)


def grounded_program(files:iter=(), inline:str=None, **kwargs_to_solver) -> str:
    "Return full grounded program, ready to be used by solve_from_grounded"
    if 'options' not in kwargs_to_solver:
        kwargs_to_solver['options'] = ''
    kwargs_to_solver['options'] += ' --mode=gringo'
    stdout, stderr = solve(files=files, inline=inline, return_raw_output=True, **kwargs_to_solver)
    return stdout
