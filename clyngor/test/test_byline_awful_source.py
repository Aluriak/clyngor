
from clyngor import ASP
from clyngor.asp_parsing import byline_parser
from clyngor.asp_parsing.byline_parser import SourceBlock


AWFUL_SOURCE = """
% this is a header
%*
a multiline one
%%*
*%  % should be saved

%* this is a comment, inlined with a rule *% rel(a,(b;c;d;e)). %* *% rel(b,c) %

.


% a comment before a rule
p(X):- q(X) ; not rel(a,X).

%* a multiline comment
before a rule
*%
p(X):- q(X,"%* text *% text %*") ; not rel(a,X).


p(X):- q(X) % a comment inside a rule
       ; not %* *% rel(a%*,Y).*% , X)
       .

% metaprogramming
#show. % do not show anything
% except…
#show p/1.
#show rel/2.
"""


def test_solving():
    """Prove that the program is valid"""
    answers = tuple(ASP(AWFUL_SOURCE).by_predicate)
    assert len(answers) == 1
    for idx, answer in enumerate(answers):
        assert 'p' not in answer
        assert len(answer['rel']) == 5
        assert answer['rel'] == {('a', 'b'), ('a', 'c'), ('a', 'd'), ('a', 'e'), ('b', 'c')}


# def test_byline_parsing():
    # for line in byline_parser.parse(AWFUL_SOURCE):
        # print(line)
    # assert False


def test_byline_clusterize():
    clusters = tuple(byline_parser.clusterize(byline_parser.parse(AWFUL_SOURCE)))
    assert clusters == (
        SourceBlock(False, (
            (1, 1, 'comment', (1, 19), ' this is a header'),
            (2, 5, 'multicomment', (20, 45), '\na multiline one\n%%*\n'),
            (5, 5, 'comment', (47, 64), ' should be saved')
        ), start=1, end=5),
        SourceBlock(True, (
            (7, 7, 'multicomment', (66, 110), ' this is a comment, inlined with a rule '),
            (7, 7, 'code', (111, 127), 'rel(a,(b;c;d;e))'),
            (7, 7, 'end', (127, 128), '.'),
            (7, 7, 'multicomment', (129, 134), ' '),
            (7, 7, 'code', (135, 144), 'rel(b,c) '),
            (7, 7, 'comment', (144, 145), ''),
            (9, 9, 'end', (147, 148), '.')
        ), start=7, end=9),
        SourceBlock(True, (
            (12, 12, 'comment', (151, 176), ' a comment before a rule'),
            (13, 13, 'code', (177, 203), 'p(X):- q(X) ; not rel(a,X)'),
            (13, 13, 'end', (203, 204), '.')
        ), start=12, end=13),
        SourceBlock(True, (
            (15, 17, 'multicomment', (206, 245), ' a multiline comment\nbefore a rule\n'),
            (18, 18, 'code', (246, 257), 'p(X):- q(X,'),
            (18, 18, 'text', (257, 277), '%* text *% text %*'),
            (18, 18, 'code', (277, 293), ') ; not rel(a,X)'),
            (18, 18, 'end', (293, 294), '.')
        ), start=15, end=18),
        SourceBlock(True, (
            (21, 21, 'code', (297, 309), 'p(X):- q(X) '),
            (21, 21, 'comment', (309, 334), ' a comment inside a rule'),
            (22, 22, 'code', (342, 348), '; not '),
            (22, 22, 'multicomment', (348, 353), ' '),
            (22, 22, 'code', (354, 359), 'rel(a'), (22, 22, 'multicomment', (359, 367), ',Y).'),
            (22, 23, 'code', (368, 380), ', X)\n       '),
            (23, 23, 'end', (380, 381), '.')
        ), start=21, end=23),
        SourceBlock(True, (
            (25, 25, 'comment', (383, 400), ' metaprogramming'),
            (26, 26, 'code', (401, 406), '#show'),
            (26, 26, 'end', (406, 407), '.'),
            (26, 26, 'comment', (408, 430), ' do not show anything'),
            (27, 27, 'comment', (431, 440), ' except…'),
            (28, 28, 'code', (441, 450), '#show p/1'),
            (28, 28, 'end', (450, 451), '.'),
            (29, 29, 'code', (452, 463), '#show rel/2'),
            (29, 29, 'end', (463, 464), '.')
        ), start=25, end=29)
    )

