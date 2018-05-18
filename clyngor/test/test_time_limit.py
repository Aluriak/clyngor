import pytest
from clyngor import solve


@pytest.mark.slow
def test_time_limit_with_solutions():
    """Sudoku yield thousands of solution in a second"""
    answers = solve([], inline=SUDOKU, options='--time-limit=1')
    nb_answer = sum(1 for answer in answers)
    assert nb_answer > 1


@pytest.mark.slow
def test_time_limit_no_solutions():
    """Queens do not yield any solution in a second
    (at least on not so powerful machines)

    This is tested because clingo do not raise the same error code
    depending of whether a solution was found or not when stopped
    because of the --time-limit option.

    """
    answers = solve([], inline=QUEENS, options='--time-limit=1')
    nb_answer = sum(1 for answer in answers)
    assert nb_answer == 0


@pytest.mark.slow
def test_no_time_limit_queens():
    """Queens yield at least one solution when enough time is provided.

    This is tested in order to prove that the time limit option works
    properly in the `test_time_limit_no_solutions` function.

    """
    answers = solve([], inline=QUEENS, nb_model=1)
    assert sum(1 for answer in answers) == 1


QUEENS = """
#const n = 200.
n(1..n).

q(X,Y) :- n(X), n(Y), not not q(X,Y).

        c(r,X; c,Y) :- q(X,Y).
not not c(r,N; c,N) :- n(N).

n(r,X,Y-1,X,Y; c,X-1,Y,X,Y; d1,X-1,Y-1,X,Y;     d2,X-1,Y+1,X,Y      ) :- n(X), n(Y).
c(r,N,0;       c,0,N;       d1,N-1,0; d1,0,N-1; d2,N-1,n+1; d2,0,N+1) :- n(N).

c(C,XX,YY) :-     c(C,X,Y), n(C,X,Y,XX,YY), not q(XX,YY).
           :- not c(C,X,Y), n(C,X,Y,XX,YY),     q(XX,YY).

#show q/2.
"""


SUDOKU = """
val(1..9).
border(1;4;7).

% Only one number per square.
1 { x(X,Y,N) : val(N) } 1 :- val(X) ; val(Y).

% Same numbers does not share row or column…
1 { x(X,Y,N) : val(X) } 1 :- val(N) ; val(Y).
1 { x(X,Y,N) : val(Y) } 1 :- val(N) ; val(X).

% … nor boxes.
1 { x(X,Y,N) : val(X), val(Y), X1<=X, X<=X1+2, Y1<=Y, Y<=Y1+2 } 1 :- val(N) ; border(X1) ; border(Y1).
"""
