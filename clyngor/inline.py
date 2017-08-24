"""Definition of the easy to integrate ASP code.

"""


from clyngor import solve
from clyngor.answers import Answers


def ASP(source_code:str):
    """Return the answer sets obtained by running the solver
    on given raw source code.

    source_code -- ASP source code

    """
    return Answers(solve(files=(), inline_source=source_code))
