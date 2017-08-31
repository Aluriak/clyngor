"""Definition of the ASP grammar"""


import arpeggio as ap


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
