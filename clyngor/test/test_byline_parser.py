
from pprint import pprint
import pytest
from clyngor import ASP
from clyngor.asp_parsing import byline_parser
from clyngor.asp_parsing.byline_parser import SourceBlock


def test_solving():
    """Prove that the program is valid"""
    answers = tuple(ASP(ASP_SOURCE).by_predicate)
    assert len(answers) == 1
    for idx, answer in enumerate(answers):
        assert len(answer['p']) == 4
        assert len(answer['rel']) == 4
        assert answer['rel'] == {('a', 'b'), ('a', 'c'), ('a', 'd'), ('a', 'e')}


def test_byline_parsing():
    parsed = tuple(byline_parser.parse(ASP_SOURCE))
    pprint(parsed)
    assert parsed == (
        (0, 0, 'empty'),
        (1, 1, 'comment', (1, 19), ' this is a header'),
        (2, 4, 'multicomment', (20, 45), '\na multiline one %%*\n'),
        (5, 5, 'empty'),
        (6, 6, 'comment', (47, 72), ' a comment before a rule'),
        (7, 7, 'code', (73, 89), 'rel(a,(b;c;d;e))'),
        (7, 7, 'end', (89, 90), '.'),
        (8, 8, 'empty'),
        (9, 11, 'multicomment', (92, 131), ' a multiline comment\nbefore a rule\n'),
        (12, 12, 'code', (132, 147), 'p(X):- rel(a,X)'),
        (12, 12, 'end', (147, 148), '.'),
        (13, 13, 'comment', (149, 167), ' and after a rule'),
        (14, 14, 'empty'),
        (15, 15, 'comment', (169, 177), ' footer'),
        (16, 16, 'comment', (178, 189), '#show p/1.'),
        (17, 17, 'comment', (190, 203), '#show rel/2.'),
    )


def test_byline_rebuild():
    clusters = byline_parser.clusterize_from_source(ASP_SOURCE)
    rebuilt = byline_parser.rebuild_clusters(clusters)
    assert rebuilt == ASP_SOURCE.strip()


def test_line_ends():
    indexes = tuple(byline_parser.lines_end('\na\nb\ncde\n\n'))
    assert indexes == (0, 2, 4, 8, 9)


def test_clusterize():
    clusters = tuple(byline_parser.clusterize(byline_parser.parse(ASP_SOURCE)))
    print(clusters)
    clusters_from_source = tuple(byline_parser.clusterize_from_source(ASP_SOURCE))
    assert clusters == clusters_from_source
    expected = (
        SourceBlock(False, (
            (1, 1, 'comment', (1, 19), ' this is a header'),
            (2, 4, 'multicomment', (20, 45), '\na multiline one %%*\n')
        ), 1, 4),
        SourceBlock(True, (
            (6, 6, 'comment', (47, 72), ' a comment before a rule'),
            (7, 7, 'code', (73, 89), 'rel(a,(b;c;d;e))'),
            (7, 7, 'end', (89, 90), '.')
        ), 6, 7),
        SourceBlock(True, (
            (9, 11, 'multicomment', (92, 131), ' a multiline comment\nbefore a rule\n'),
            (12, 12, 'code', (132, 147), 'p(X):- rel(a,X)'),
            (12, 12, 'end', (147, 148), '.'),
            (13, 13, 'comment', (149, 167), ' and after a rule')
        ), 9, 13),
        SourceBlock(False, (
            (15, 15, 'comment', (169, 177), ' footer'),
            (16, 16, 'comment', (178, 189), '#show p/1.'),
            (17, 17, 'comment', (190, 203), '#show rel/2.')
        ), 15, 17)
    )
    assert clusters == expected


def test_clusterize_over_blocks():
    parsed = tuple(byline_parser.parse(ASP_SOURCE_RULE_OVER_BLOCKS))
    pprint(parsed)
    clusters = tuple(byline_parser.clusterize(parsed))
    clusters_from_source = tuple(byline_parser.clusterize_from_source(ASP_SOURCE_RULE_OVER_BLOCKS))
    assert clusters == clusters_from_source
    pprint(clusters)
    expected = (
        SourceBlock(True, (
            (1, 1, 'comment', (1, 12), ' comment 1'),
            (2, 2, 'code', (13, 19), 'rel(a)'),
            (3, 3, 'comment', (20, 31), ' comment 2'),
            (5, 5, 'comment', (33, 44), ' comment 3'),
            (6, 6, 'end', (45, 46), '.'),
            (7, 7, 'comment', (47, 58), ' comment 4'),
        ), 1, 7),
    )
    assert clusters == expected


ASP_SOURCE = """
% this is a header
%*
a multiline one %%*
*%

% a comment before a rule
rel(a,(b;c;d;e)).

%* a multiline comment
before a rule
*%
p(X):- rel(a,X).
% and after a rule

% footer
%#show p/1.
%#show rel/2.
"""


ASP_SOURCE_RULE_OVER_BLOCKS = """
% comment 1
rel(a)
% comment 2

% comment 3
.
% comment 4
"""
