
from clyngor import ASP
from clyngor.asp_parsing import byline_parser
from clyngor.asp_parsing.byline_parser import SourceBlock


AWFUL_SOURCE = """
% this is a header
%*
a multiline one
%%*
*% % should be saved

%* this is a comment, inlined with a rule *% rel(a,(b;c;d;e)). %* *% rel(b,c) %

    .


% a comment before a rule
p(X):- q(X) ; not rel(a,X).

%* a multiline comment
before a rule
*%
p(X):- q(X,"%* text *% text %*") ; not rel(a,X).


p(X):- q(X) % a comment inside a rule
    ; not %* *% rel(a %*,Y).*% , X)
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


def test_byline_rebuild():
    clusters = byline_parser.clusterize_from_source(AWFUL_SOURCE)
    rebuilt = byline_parser.rebuild_clusters(clusters, sep_comment=' ')
    lines = AWFUL_SOURCE.splitlines()
    # not all lines are conserved. Blank ones are discarded by rebuilding
    expected = lines[:8] + lines[9:10] + lines[11:19] + lines[20:]
    assert rebuilt == '\n'.join(expected).strip()


def test_byline_clusterize():
    clusters = tuple(byline_parser.clusterize(byline_parser.parse(AWFUL_SOURCE)))

    index, last_line_index = 1, None
    def entry(start, end, type, content, spacing:int=0) -> tuple:
        """Produce a line to put in a cluster. Automatically count the position"""
        nonlocal index, last_line_index
        if last_line_index is None:
            last_line_index = start
        types_size = {'comment': 1, 'multicomment': 4, 'code': 0, 'end': 0, 'text': 2}
        index += spacing + (start - last_line_index)  # take account of line break
        start_index = index
        index += len(content) + types_size[type]
        last_line_index = end
        return (start, end, type, (start_index, index), content)

    assert len(clusters) == 6
    assert clusters[0] == SourceBlock(
        False, (
            entry(1, 1, 'comment', ' this is a header'),
            entry(2, 5, 'multicomment', '\na multiline one\n%%*\n'),
            entry(5, 5, 'comment', ' should be saved', spacing=1)
        ), start=1, end=5
    )
    assert clusters[1] == SourceBlock(
        True, (
            entry(7, 7, 'multicomment', ' this is a comment, inlined with a rule '),
            entry(7, 7, 'code', 'rel(a,(b;c;d;e))', spacing=1),
            entry(7, 7, 'end', '.'),
            entry(7, 7, 'multicomment', ' ', spacing=1),
            entry(7, 7, 'code', 'rel(b,c)', spacing=1),
            entry(7, 7, 'comment', '', spacing=1),
            entry(9, 9, 'end', '.', spacing=4)
        ), start=7, end=9
    )
    assert clusters[2] == SourceBlock(
        True, (
            entry(12, 12, 'comment', ' a comment before a rule'),
            entry(13, 13, 'code', 'p(X):- q(X) ; not rel(a,X)'),
            entry(13, 13, 'end', '.')
        ), start=12, end=13
    )
    assert clusters[3] == SourceBlock(
        True, (
            entry(15, 17, 'multicomment', ' a multiline comment\nbefore a rule\n'),
            entry(18, 18, 'code', 'p(X):- q(X,'),
            entry(18, 18, 'text', '%* text *% text %*'),
            entry(18, 18, 'code', ') ; not rel(a,X)'),
            entry(18, 18, 'end', '.')
        ), start=15, end=18
    )
    assert clusters[4] == SourceBlock(
        True, (
            entry(21, 21, 'code', 'p(X):- q(X)'),
            entry(21, 21, 'comment', ' a comment inside a rule', spacing=1),
            entry(22, 22, 'code', '; not', spacing=4),
            entry(22, 22, 'multicomment', ' ', spacing=1),
            entry(22, 22, 'code', 'rel(a', spacing=1),
            entry(22, 22, 'multicomment', ',Y).', spacing=1),
            entry(22, 22, 'code', ', X)', spacing=1),
            entry(23, 23, 'end', '.', spacing=4)
        ), start=21, end=23
    )
    assert clusters[5] == SourceBlock(
        True, (
            entry(25, 25, 'comment', ' metaprogramming'),
            entry(26, 26, 'code', '#show'),
            entry(26, 26, 'end', '.'),
            entry(26, 26, 'comment', ' do not show anything', spacing=1),
            entry(27, 27, 'comment', ' except…'),
            entry(28, 28, 'code', '#show p/1'),
            entry(28, 28, 'end', '.'),
            entry(29, 29, 'code', '#show rel/2'),
            entry(29, 29, 'end', '.')
        ), start=25, end=29
    )

