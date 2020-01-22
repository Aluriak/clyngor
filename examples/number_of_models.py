

import clyngor

models = clyngor.solve(inline='1{n(1..1000)}1.', nb_model=500, stats=True)

nb_model_found = 0
for nb_model_found, model in enumerate(models, start=1):
    pass

nb_model_announced = models.statistics['Models']


print(f'Number of models    found by clyngor: {nb_model_found}')
print(f'Number of models announced by clingo: {nb_model_announced}')
