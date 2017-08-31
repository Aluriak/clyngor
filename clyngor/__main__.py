
from clyngor import ASP


ASP_CODE = """
rel(a,c). rel(a,d). rel(b,d). rel(b,e).
obj(X):- rel(X,_) ; rel(X,Y): att(Y).
att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
:- not obj(X):obj(X).
:- not att(Y):att(Y).
"""


if __name__ == '__main__':
    answers = ASP(ASP_CODE)
    for answer in answers.by_predicate.first_arg_only:
        print('{' + ','.join(answer['obj']) + '} × {' + ','.join(answer['att']) + '}')
