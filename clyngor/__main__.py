
from clyngor import ASP, solve


# if __name__ == '__main__':
answers = ASP("""
rel(a,(c;d)). rel(b,(d;e)).
obj(X):- rel(X,_) ; rel(X,Y): att(Y).
att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
:- not obj(X):obj(X).
:- not att(Y):att(Y).
""")
for answer in answers.by_predicate.first_arg_only:
# for answer in answers:
    print(answer)
    print('{' + ','.join(answer['obj']) + '} × {' + ','.join(answer['att']) + '}')
