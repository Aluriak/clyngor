"""Routines for answer set parsing.

"""
import re


import arpeggio as ap


class CollapsableAtomVisitor(ap.PTNodeVisitor):
    """Implement both the grammar and the way to handle it, dedicated to the
    parsing of ASP like string to produce frozenset instances.

    collapse_args: function terms in predicate arguments are collapsed into strings
    collapse_atoms: atoms (predicate plus terms) are collapsed into strings
                   requires that collapse_args is True

    See Parser class for usage examples.

    """
    def __init__(self, collapse_args:bool=True, collapse_atoms:bool=False,
                 parse_integer:bool=True):
        super().__init__()
        self.collapse_args = bool(collapse_args)
        self.collapse_atoms = bool(collapse_atoms)
        self._int_builder = int if parse_integer else str

    def visit_number(self, node, children):
        return self._int_builder(node.value)

    def visit_args(self, node, children):
        return children

    def visit_aloneargs(self, node, children):
        return self.visit_term(node, ('', *children))

    def visit_text(self, node, children):
        text = tuple(children)[0] if children else ''
        return '"' + text + '"'

    def visit_subterm(self, node, children):
        predicate, *args = children
        if self.collapse_args:
            return (predicate + '(' + ','.join(map(str, *args)) + ')') if args else predicate
        else:
            return (predicate, tuple(args[0])) if args else predicate

    def visit_term(self, node, children):
        predicate, *args = children
        if self.collapse_atoms:
            return (predicate + '(' + ','.join(map(str, *args)) + ')') if args else predicate
        else:
            return (predicate, (tuple(args[0]) if args else ()))

    def visit_terms(self, node, children):
        return frozenset(children)

    @staticmethod
    def grammar():
        def ident():      return ap.RegExMatch(r'[a-z][a-zA-Z0-9_]*')
        def number():     return ap.RegExMatch(r'-?[0-9]+')
        def text():       return '"', ap.RegExMatch(r'((\\")|([^"]))*'), '"'
        def litteral():   return [text, number]
        def subterm():    return [(ident, ap.Optional("(", args, ")")), litteral, aloneargs]
        def args():       return subterm, ap.ZeroOrMore(',', subterm)
        def aloneargs():  return '(', args, ')'
        # NB: litteral outputed by #show are not handled.
        def term():       return ident, ap.Optional("(", args, ")")
        def terms():      return ap.ZeroOrMore(term)
        return terms


class Parser:
    def __init__(self, collapse_atoms=False, collapse_args=True, callback=None,
                 parse_integer:bool=True):
        """
        collapse_args -- function terms in predicate arguments are collapsed into strings
        collapse_atoms -- atoms (predicate plus terms) are collapsed into strings
                          requires that collapse_args is True
        parse_integer -- return integers as int instead of string

        examples:

            >>> Parser(False, True).parse_terms('a(b,c(d))')
            frozenset({('a', ('b', 'c(d)'))})

            >>> Parser(True, True).parse_terms('a(b,c(d))')
            frozenset({'a(b,c(d))'})

            >>> Parser(False, False).parse_terms('a(b,c(d))')
            frozenset({('a', ('b', ('c', ('d',))))})

            >>> Parser(False, False).parse_terms('a')
            frozenset({('a', ())})

            >>> Parser(True, False).parse_terms('a(b,c(d))')  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            ValueError

            >>> Parser(parse_integer=False).parse_terms('a(3)')
            frozenset({('a', ('3',))})

            >>> Parser().parse_terms('a(3)')
            frozenset({('a', (3,))})

        """
        self.collapse_args = bool(collapse_args)
        self.collapse_atoms = bool(collapse_atoms)
        self.atom_visitor = CollapsableAtomVisitor(
            bool(collapse_args),
            bool(collapse_atoms),
            parse_integer
        )
        self.grammar = self.atom_visitor.grammar()
        self.callback = callback
        if self.collapse_atoms and not self.collapse_args:
            raise ValueError("if atoms are collapsed, terms must"
                             " also be collapsed!")


    def parse_terms(self, string:str) -> frozenset:
        """Return the frozenset computed from given valid ASP-compliant string"""
        parse_tree = ap.ParserPython(self.grammar).parse(string)
        if parse_tree:
            return ap.visit_parse_tree(parse_tree, self.atom_visitor)
        else:
            return frozenset()

    # alias
    parse = parse_terms


    def parse_clasp_output(self, output:iter or str, *, yield_stats:bool=False,
                           yield_info:bool=False, yield_prgs:bool=False):
        """Decorator over the parse_clasp_output module function,
        where the answers are parsed using self.parse_terms method.

        """
        parsed = parse_clasp_output(output, yield_stats=yield_stats,
                                    yield_info=yield_info,
                                    yield_prgs=yield_prgs)
        for type, payload in parsed:
            if type == 'answer':
                yield type, self.parse_terms(payload)
            else:
                yield type, payload


def parse_clasp_output(output:iter or str, *, yield_stats:bool=False,
                       yield_opti:bool=True, yield_info:bool=False,
                       yield_prgs:bool=False):
    """Yield pairs (payload type, payload) where type is 'info', 'statistics',
    'optimization', 'progression', or 'answer' and payload the raw information.

    output -- iterable of lines or full clasp output to parse
    yield_stats -- yields final statistics as a mapping {field: value}
                   under type 'statistics'
    yield_opti  -- yields line sometimes following an answer set,
                   beginning with 'Optimization: '.
    yield_info  -- yields all lines not included in other types, including the
                   first lines not related to first answer
                   under type 'info' as a tuple of lines
    yield_prgs -- yields lines of Progressions that are sometimes
                  following an answer set in multithreading contexts,
                  under type 'progression' as a string.

    In any case, tuple ('answer', termset) will be returned
    with termset a string containing the raw data.

    """
    ASW_FLAG, OPT_FLAG, PROGRESS = 'Answer: ', 'Optimization: ', 'Progression :'
    output = iter(output.splitlines() if isinstance(output, str) else output)

    # get the first lines
    line = next(output)
    infos = []
    while not line.startswith(ASW_FLAG):
        infos.append(line)
        try:
            line = next(output)
        except StopIteration:
            return

    # first answer begins
    while True:
        if line.startswith(ASW_FLAG):
            yield 'answer', next(output)
        elif line.startswith(OPT_FLAG) and yield_opti:
            yield 'optimization', tuple(map(int, line[len(OPT_FLAG):].strip().split()))
        elif line.startswith(PROGRESS) and yield_prgs:
            yield 'progression', line[len(PROGRESS):].strip()
        elif not line.strip():  # empty line: statistics are beginning
            if not yield_stats: break  # stats are the last part of the output
            stats = {}
            for line in output:
                sep = line.find(':')
                key, value = line[:sep], line[sep+1:]
                stats[key.strip()] = value.strip()
            yield 'statistics', stats
            break
        else:  # should not happen
            infos.append(line)
        try:
            line = next(output)
        except StopIteration:
            break

    if yield_info:
        yield 'info', tuple(infos)

parse_clasp_output.out_types = ('info', 'answers', 'optimization, ''statistics')  # the order is the one in clingo input


def validate_clasp_stderr(stderr:iter or str) -> iter:
    """Parse stderr of clingo, detect and yield defects lines in form of dict"""
    reg_err = re.compile(r'(.+):([0-9]+):([0-9]+)-([0-9]+): (\w+): (.+)')
    while True:
        try:
            line = next(stderr).strip()
        except StopIteration:
            return
        err_match = reg_err.fullmatch(line)
        if err_match:
            data = dict(zip(('filename', 'lineno', 'char_beg', 'char_end', 'level', 'message'), err_match.groups()))
            for int_field in ('lineno', 'char_beg', 'char_end'):
                data[int_field] = int(data[int_field])
            data['text'] = line
            data['human message'] = '{} in file {} at line {} and column {}-{}'.format(
                data['message'].strip(':,'), data['filename'], data['lineno'], data['char_beg'], data['char_end']
            )

            # special cases
            if 'atom does not occur in any rule head' in data['text']:
                data['atom'] = next(stderr).strip()
                data['human message'] = "atom '{}' does not occur in any rule head in file {} at line {} and column {}-{}".format(
                    data['atom'], data['filename'], data['lineno'], data['char_beg'], data['char_end']
                )
            yield data
