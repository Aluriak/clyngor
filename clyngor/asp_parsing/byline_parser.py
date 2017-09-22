"""Routines working on ASP source in order to parse them, line by line instead
of a whole.

"""

import math
import itertools
from bisect import bisect_left
from collections import defaultdict, namedtuple
import arpeggio as ap


SourceBlock = namedtuple('SourceBlock', 'have_code, lines, start, end')
def SourceBlock__from_raw(have_code, lines, start, end):
    return SourceBlock(bool(have_code), tuple(lines), int(start), int(end))
SourceBlock.from_raw = SourceBlock__from_raw


def parse(asp_source_code:str) -> iter:
    """Parse the source code into hierarchy of lines"""
    parser = ap.ParserPython(line_grammar())
    parse_tree = parser.parse(asp_source_code)
    parsed_lines = ap.visit_parse_tree(parse_tree, LinesExtractor())
    return with_line_number(parsed_lines, asp_source_code)


def clusterize_from_source(source_code:str) -> tuple:
    """Return the clusterized source code, parsed into blocks"""
    return tuple(clusterize(parse(source_code)))


def rebuild_clusters(clusters:str, sep_cluster:str='\n\n', sep_comment:str='  ',
                     rule_indent:str='    ') -> str:
    """Return the source code inferred from given clusters.

    """
    return sep_cluster.join(cluster_as_string(cluster, sep_comment, rule_indent)
                            for cluster in clusters)


def cluster_as_string(cluster:SourceBlock, sep_comment:str, rule_indent:str) -> str:
    """Return a string representation of given cluster"""
    COMMENTS = {'comment', 'multicomment'}
    CODE = {'code', 'end'}
    pretty_doc = lambda cluster: '\n'.join(line[4] for line in cluster.lines)
    previous_line_end = None
    previous_type = None
    out = ''
    in_code = False

    def spacing() -> str:
        if not new_line:
            if previous_type in COMMENTS:
                return sep_comment
            elif previous_type in CODE and type in COMMENTS:
                return sep_comment
        elif new_line and not first_line:
            if in_code:  # put indentation
                return '\n' + rule_indent
            else:
                return '\n'
        return ''

    for line_start, line_end, type, _, data in cluster.lines:
        assert line_end is not None
        assert line_start is not None
        first_line = previous_line_end is None
        new_line = first_line or line_start != previous_line_end
        out += spacing()
        if type == 'comment':
            out += '%' + data
        if type == 'multicomment':
            out += '%*' + data + '*%'
        if type == 'code':
            in_code = True
            out += data
        if type == 'end':
            if not in_code:  # if in_code is True, there is a problem
                print("MISUTD: unexpected '.' during parsing of non-code segment")
            in_code = False
            out += data
        if type == 'text':
            out += '"' + data + '"'
        previous_line_end = line_end
        previous_type = type
    return out


def clusterize(parsed_lines:iter) -> [SourceBlock]:
    """Yield SourceBlock instances.

    """
    line_type = lambda line: line[2]
    have_code = lambda line: 'code' == line_type(line)
    have_end = lambda line: 'end' == line_type(line)
    empty = lambda line: 'empty' == line_type(line)

    state_code = False
    code_in_cluster, current_cluster, start, end = False, [], math.inf, 0

    for line in parsed_lines:
        if empty(line):
            if not state_code and current_cluster:
                yield SourceBlock.from_raw(code_in_cluster, current_cluster, start, end)
                code_in_cluster, current_cluster, start, end = False, [], math.inf, 0
            continue
        start = min(start, line[0])
        end = max(end, line[1])
        if state_code and not have_end(line):
            current_cluster.append(line)
        elif have_code(line):
            assert not have_end(line)
            state_code = True
            code_in_cluster = True
            current_cluster.append(line)
        elif have_end(line):
            assert not have_code(line)
            assert state_code, "input source is not valid ; dot arrives before rules"
            state_code = False
            current_cluster.append(line)
        else:  # line is just free doc
            current_cluster.append(line)
    if current_cluster:
        yield SourceBlock.from_raw(code_in_cluster, current_cluster, start, end)


def build_line_index(parsed_lines:iter) -> dict:
    """Maps each line number with its content"""
    index = defaultdict(list)
    for full_line in parsed_lines:
        line_start, line_end, *data = full_line
        for line in range(line_start, line_end + 1):
            index[line].append(full_line)
    for line in range(max(index.keys())):  # create empty lines
        index[line]
    return {line: tuple(data) for line, data in index.items()}


def with_line_number(parsed_lines:iter, source:str) -> iter:
    lines = tuple(lines_end(source))
    line_of = lambda position: bisect_left(lines, position)
    previous_line_end = 0
    for line in parsed_lines:
        start_pos, end_pos = map(line_of, line[1])
        if start_pos > previous_line_end:
            yield previous_line_end, start_pos-1, 'empty'
        yield (start_pos, end_pos, *line)
        previous_line_end = end_pos+1


def lines_end(source:str) -> list:
    """Yield the position of each line end in source

    >>> tuple(lines_end('\\n'))
    (0,)
    >>> tuple(lines_end('\\na\\n'))
    (0, 2)
    >>> tuple(lines_end('\\na\\nb\\ncde\\n\\n'))
    (0, 2, 4, 8, 9)

    """
    size = 0
    for line in source.splitlines(True):
        yield len(line) + size - 1
        size += len(line)


def line_grammar():
    """Implement the Answer Set Programming grammar.

    """
    def text():         return ap.Sequence('"', ap.RegExMatch(r'((\\")|([^"]))*'), '"', skipws=False)
    def comment():      return ap.RegExMatch(r'%.*$'),
    def multiline_comment(): return ap.RegExMatch(r'%\*.*?\*%', multiline=True),
    def asp_code():     return ap.RegExMatch(r'[^%"\.]*[^%"\.\s]', multiline=True),
    def rule_end():     return '.',
    def program():      return ap.OneOrMore([text, multiline_comment, comment, asp_code, rule_end])

    return program


class LinesExtractor(ap.PTNodeVisitor):
    def __init__(self):
        super().__init__()

    def visit_text(self, node, children):
        # print(node.name, dir(node))
        # print(node.position, node.position_end, node.comments)
        # print(children)
        return 'text', (node.position, node.position_end), children[0]

    def visit_comment(self, node, children):
        assert children[0].startswith('%')
        return 'comment', (node.position, node.position_end), children[0][1:]

    def visit_multiline_comment(self, node, children):
        assert len(children) == 1
        assert children[0].endswith('*%')
        assert children[0].startswith('%*')
        assert len(children[0]) >= 4
        data = children[0][2:-2]
        return 'multicomment', (node.position, node.position_end), data

    def visit_asp_code(self, node, children):
        # data = children[0].strip('\n')
        # return 'code', (node.position, node.position + len(data) - 1), data
        return 'code', (node.position, node.position_end), children[0]

    def visit_rule_end(self, node, children):
        return 'end', (node.position, node.position_end), '.'

    def visit_program(self, node, children):
        return tuple(children)
