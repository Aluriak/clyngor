"""Handling asprin with clyngor.

The goal is to programatically run and retrieve answer sets
from asprin. Because asprin uses the same output format as clingo,
it is possible to plug asprin instead.

If no file is given in command line argument, the example1 of asprin source code
will be used.

asprin: https://github.com/potassco/asprin
asprin examples: https://github.com/potassco/asprin/tree/master/asprin/examples
clyngor: https://github.com/aluriak/clyngor

This require the installation of the asprin package,
and therefore the clingo package.

    git clone https://github.com/potassco/asprin && cd asprin
    python setup.py install  # you should use a virtualenv
    … # install clingo python package (you will need to compile it from sources)

Now, you can run the asprin command, and therefore let clyngor do it for you.

"""

import sys
import clyngor

clyngor.CLINGO_BIN_PATH = 'asprin'  # use installed asprin, not clingo directly

ASPRIN_CODE = """
dom(1..3).
1 { a(X) : dom(X) }.
#show a/1.

#preference(p,subset) {a(X)}.
#optimize(p).
"""

args = sys.argv[1:]
if not args:
    print('No file provided: a default example will be run.')

models = clyngor.solve(
    args,  # list of files to run
    inline='' if args else ASPRIN_CODE,  # add default content if no file provided
    use_clingo_module=False,  # don't use the clingo module, just parse the output
    nb_model=None  # asprin doesn't support the -n parameter
)
# models.by_predicate  # uncomment to get models in {predicate: {args}} instead of {(pred, args)}
for idx, model in enumerate(models, start=1):
    print(idx, model)
