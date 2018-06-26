"""Definition of the easy to integrate ASP code.

"""


from clyngor import solve


def ASP(source_code:str, **kwargs):
    """Return the answer sets obtained by running the solver
    on given raw source code.

    source_code -- ASP source code
    kwargs -- keyword arguments to be given to solve() call

    """
    return solve(inline=source_code, stats=False, **kwargs)


def ASP_last_model(source_code:str, **kwargs):
    """Return the last answer set obtained by running the solver
    on given raw source code.

    source_code -- ASP source code
    kwargs -- keyword arguments to be given to solve() call

    Assuming that given source code is running with an optimization
    and with no --opt-mode option, this function returns an optimal model.

    """
    model = None
    for model in solve(inline=source_code, stats=False, **kwargs):
        pass
    return model


def ASP_one_model(source_code:str, **kwargs):
    """Return the first answer set obtained by running the solver
    on given raw source code.

    source_code -- ASP source code
    kwargs -- keyword arguments to be given to solve() call

    """
    models = solve(inline=source_code, stats=False, nb_model=1, **kwargs)
    return next(models, None)


# shortcuts
ASP.best_model = ASP_last_model
ASP.one_model = ASP_one_model
ASP.all_models = ASP
