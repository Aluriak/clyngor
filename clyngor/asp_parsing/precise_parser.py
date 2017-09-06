"""Routines and classes for Answer Set Programming source code parsing.

This parser is precise: it will carefully parse all asp source code
(except the comments).

For a more high level parser, see byline_parser.

"""

import arpeggio as ap

from clyngor.asp_parsing import asp_grammar, asp_grammar_comments
from clyngor.asp_parsing import alt_parse


def parse_asp_program_by_arpeggio(asp_source_code:str, do=None, have_comments:bool=True) -> tuple:
    parser = ap.ParserPython(asp_grammar(), asp_grammar_comments if have_comments else None)
    parse_tree = parser.parse(asp_source_code)
    return ap.visit_parse_tree(parse_tree, visitor=do or CodeAsTuple())

def parse_asp_program_by_pypeg(asp_source_code:str, do=None, have_comments:bool=True) -> tuple:
    return alt_parse.parse_asp(asp_source_code)

# handles multiline comments, but is slower
parse_asp_program = parse_asp_program_by_pypeg
parse_asp_program = parse_asp_program_by_arpeggio


class CodeAsTuple(ap.PTNodeVisitor):
    def __init__(self, int_builder:type=int):
        super().__init__()
        self._int_builder = int_builder

    def visit_number(self, node, children):
        return self._int_builder(node.value)

    def visit_args(self, node, children):
        return tuple(children)

    def visit_multargs(self, node, children):
        if len(children) > 1:
            return ('disjunction', *children)
        return tuple(children)


    def visit_text(self, node, children):
        if len(children) == 0:  # empty text
            text = ''
        else:
            assert len(children) == 1
            text = tuple(children)[0]
        return 'text', str(text)

    def visit_ident(self, node, children):
        return str(node.value)

    def visit_unnamedterm(self, node, children):
        # children is a list of element in disjunction
        assert len(children) == 1
        args = children[0]
        if args[0] == 'disjunction':
            return args
        return 'term', None, tuple(children)

    def visit_namedterm(self, node, children):
        assert len(children) in {1, 2}
        if len(children) == 1:  # just an ident
            predicate, args = children[0], ()
        else:  # ident + args
            predicate, args = children
            if len(args) > 1:  # disjunction
                args = ('disjunction', *args)
            else:
                assert len(args) == 1
                args = args[0]
        return 'term', predicate, tuple(args)

    def visit_not_term(self, node, children):
        assert len(children) == 1
        type, predicate, args = children[0]
        return '¬' + type, predicate, args

    def visit_term(self, node, children):
        assert len(children) == 1
        type, predicate, args = children[0]
        return type, predicate, args

    def visit_not_forall(self, node, children):
        atom, *conditions = children
        assert len(atom) == 3
        assert atom[0] == 'term'
        return '¬forall', atom[1], atom[2], tuple(conditions)

    def visit_forall(self, node, children):
        atom, *conditions = children
        assert len(atom) == 3
        assert atom[0] == 'term'
        return 'forall', atom[1], atom[2], tuple(conditions)

    def visit_expression(self, node, children):
        return tuple(children)

    def visit_body(self, node, children):
        predicate, *args = children
        for child in children:
            assert len(child) == 1
        return tuple(child[0] for child in children)

    def visit_constraint(self, node, children):
        if len(children) == 1:
            children = children[0]
        else:
            raise ValueError("Constraint body has not 1 value, but {}: {}".format(len(children), children))
        return 'constraint', tuple(children)


    def visit_selection(self, node, children):
        downum, upnum, body = 0, None, ()
        if len(children) == 3:
            downum, expr, upnum = children
        elif len(children) == 1:
            expr = children[0]
        else:
            assert len(children) == 2
            if isinstance(children[0], tuple):  # second number given
                expr, upnum = children
            else:  # first number given
                upnum, expr = children
        return 'selection', downum, upnum, expr


    def visit_head(self, node, children):
        predicate, *args = children
        assert len(children) == 1
        return children[0]

    def visit_rule(self, node, children):
        assert len(children) == 2
        head, body = children
        return ('rule', tuple(head), tuple(body))

    def visit_multirule(self, node, children):
        assert len(children) > 2  # at least two heads and a body
        head, body = children[:-1], children[-1]
        return ('multirule', tuple(head), tuple(body))


    def visit_arityterm(self, node, children):
        return 'arity', children[0], self._int_builder(children[1])

    def visit_meta_show(self, node, children):
        assert len(children) == 1
        type, *child = children[0]
        return ('show/n' if type == 'arity' else 'show', *child)

    def visit_meta_const(self, node, children):
        assert len(children) == 2
        return ('const', *tuple(children))


    def visit_program(self, node, children):
        for rule in children:
            yield rule
