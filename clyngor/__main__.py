
from timeit import timeit
from pprint import pprint
from functools import partial

from clyngor import ASP


ASP_CODE = """
rel(a,c). rel(a,d). rel(b,d). rel(b,e).
obj(X):- rel(X,_) ; rel(X,Y): att(Y).
att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
:- not obj(X):obj(X).
:- not att(Y):att(Y).
"""

def time_efficiency(number:int=1000) -> float:
    def run(ASP=ASP, ASP_CODE=ASP_CODE):
        return tuple(ASP(ASP_CODE))
    return 'Perform {} calls in {} seconds.'.format(number, round(timeit(run, number=number), 2))


if __name__ == '__main__':
    answers = ASP(ASP_CODE)
    for answer in answers.by_predicate.first_arg_only:
        print('{' + ','.join(answer['obj']) + '} × {' + ','.join(answer['att']) + '}')
    print()

    print('Benchmark:')
    print(time_efficiency())
    print()
