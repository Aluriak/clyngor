"""Routines and classes for Answer Set Programming source code parsing.

"""

import re
import arpeggio as ap


def parse_asp_program(asp_program:str, do=None) -> dict:
    parse_tree = ap.ParserPython(asp_grammar()).parse(asp_program)
    return ap.visit_parse_tree(parse_tree, visitor=do or CodeAsTuple())


def asp_grammar():
    """Implement the Answer Set Programming grammar.
    """
    def ident():      return ap.RegExMatch(r'[a-z][a-zA-Z0-9_]*')
    def number():     return ap.RegExMatch(r'-?[0-9]+')
    def text():       return '"', ap.RegExMatch(r'((\\")|([^"]))*'), '"'
    def litteral():   return [ident, text, number]
    def variable():   return ap.RegExMatch(r'(([A-Z][a-zA-Z0-9_]*)|(_))')
    def subterm():    return [(ident, ap.Optional("(", args, ")")), litteral, variable]
    def args():       return subterm, ap.ZeroOrMore(',', subterm)
    def term():       return ap.Optional('not'), ident, ap.Optional("(", args, ")")
    def forall():     return term, ':', term, ap.ZeroOrMore(',', term)
    def expression(): return [forall, term]
    def body():       return expression, ap.ZeroOrMore(';', expression)
    def constraint(): return ':-', body
    def head():       return term, ap.ZeroOrMore(';', term)
    def rule():       return head, ':-', body
    def selection_nobody():  return ap.Optional(number), '{', ap.OneOrMore(expression), '}', ap.Optional(number)
    def selection_body():  return ap.Optional(number), '{', ap.OneOrMore(expression), '}', ap.Optional(number), ':-', body
    def selection():  return [selection_body, selection_nobody]
    def instruction():return [selection, constraint, rule, term]
    def program():    return ap.OneOrMore(instruction, '.')
    return program


class CodeAsTuple(ap.PTNodeVisitor):
    def __init__(self, int_builder:type=int):
        super().__init__()
        self._int_builder = int_builder

    def visit_number(self, node, children):
        return self._int_builder(node.value)

    def visit_args(self, node, children):
        return tuple(children)

    def visit_text(self, node, children):
        text = tuple(children)[0]
        return 'text', str(text)

    def visit_ident(self, node, children):
        return str(node.value)

    def visit_term(self, node, children):
        predicate, *args = children
        assert len(args) in {0, 1}
        args = args[0] if len(args) == 1 else args
        return 'term', predicate, tuple(args)

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
        return 'constraint', tuple(children)


    def visit_selection_nobody(self, node, children):
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
        return 'selection', downum, upnum, expr, body


    def visit_selection_body(self, node, children):
        downum, upnum, body = 0, None, ()
        if len(children) == 4:
            downum, expr, upnum, body = children
        elif len(children) == 2:  # no numbers
            expr, body = children
        else:  # one number is given ; which one ?
            assert len(children) == 3
            tuples = tuple(isinstance(child, tuple) for child in children)
            assert any(tuples)
            if tuples[0]:  # the second number is given
                assert not tuples[1]
                expr, upnum, body = children
            elif tuples[1]:  # the first number is given
                downum, expr, body = children
            else:  # no number given WTF
                assert False, "algorithm is false."
            # determine if body is given
        return 'selection', downum, upnum, expr, body

    def visit_head(self, node, children):
        predicate, *args = children
        return children

    def visit_rule(self, node, children):
        head, *body = children
        if len(head) == 1:  # general case: only one production
            head = head[0][1:]  # remove the 'term'
            type = 'rule'
        else:
            type = 'multirule'
        if len(body) == 1:
            body = body[0]
        else:
            raise ValueError("Body has not 1 value, but {}: {}".format(len(body), body))
        return (type, *tuple(head), tuple(body))

    def visit_program(self, node, children):
        for rule in children:
            yield rule
