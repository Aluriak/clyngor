
from timeit import timeit
from pprint import pprint
from functools import partial

from clyngor import ASP
from clyngor import asp_parsing


ASP_CODE = """
rel(a,c). rel(a,d). rel(b,d). rel(b,e).
obj(X):- rel(X,_) ; rel(X,Y): att(Y).
att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
:- not obj(X):obj(X).
:- not att(Y):att(Y).
"""

def time_efficiency():
    func = partial(asp_parsing.program_to_dependancy_graph, ASP_CODE)
    print('Perform 1000 graphs in', timeit(func, number=1000), 'seconds.')
    # last time: 3.4s


if __name__ == '__main__':
    answers = ASP(ASP_CODE)
    for answer in answers.by_predicate.first_arg_only:
        print('{' + ','.join(answer['obj']) + '} × {' + ','.join(answer['att']) + '}')
    print()

    print('Dependancy graph:')
    pprint(asp_parsing.program_to_dependancy_graph(ASP_CODE))
    print()

    print('Benchmark:')
    time_efficiency()
