"""Typical recipe to enumerate optimal models using clyngor"""


import clyngor


def opt_models_from_clyngor_answers(answers:iter, *, repeated_optimal:bool=True):
    """Return tuple of optimal models found by clingor.solve from answers.

    Available as clyngor.opt_models_from_clyngor_answers

    This function assumes that:

    - Option '--opt-mode=optN' have been given to clingo.

    - that models are yielded by clingo in increasing optimization value,
    therefore there is no need to verify that a model B succeeding a model A
    is better if they have different optimization value.

    - that the first found optimal model will be given a second time, unless option repeated_optimal is set to False.

    """
    current_opt, models = None, []
    for model, opt in answers.with_optimization:
        if opt != current_opt:
            current_opt, models = opt, []
            if not repeated_optimal:  # the first optimal model will not be given again as last model
                models.append(model)
        else:
            models.append(model)
    return tuple(models)


if __name__ == "__main__":
    # usage example
    ASP = r"""
q(1..10).
1{p(X): q(X)}3.
nb(odd,N):- N={p(X): X\2=0}.
nb(even,N):- N={p(X): X\2=1}.
nb(sum,N):- N=#sum{X:p(X)}.
#minimize{N,2:nb(odd,N)}.
#maximize{N,1:nb(even,N)}.
    """
    stdout, _ = clyngor.solve(inline=ASP, return_raw_output=True, options='--opt-mode=optN', stats=False)
    print('CLINGO OUTPUT:')
    print(stdout)
    print('\n\nPARSED OUTPUT:')
    for idx, model in enumerate(opt_models_from_clyngor_answers(clyngor.solve(inline=ASP, options='--opt-mode=optN').by_arity)):
        print(idx, ' '.join(f'p({args[0]})' for args in model['p', 1]))
