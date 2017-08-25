"""Definition of the easy to integrate ASP code.

"""


from clyngor import solve


def ASP(source_code:str):
    """Return the answer sets obtained by running the solver
    on given raw source code.

    source_code -- ASP source code

    """
    return solve(files=(), inline=source_code)
