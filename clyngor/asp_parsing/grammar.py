"""Definition of the ASP grammar"""


import arpeggio as ap


def asp_grammar():
    """Implement the Answer Set Programming grammar.

    """

    # litterals
    def ident():        return ap.RegExMatch(r'[a-z][a-zA-Z0-9_]*')
    def number():       return ap.RegExMatch(r'-?[0-9]+')
    def text():         return '"', ap.RegExMatch(r'((\\")|([^"]))*'), '"'
    def variable():     return ap.RegExMatch(r'(([A-Z][a-zA-Z0-9_]*)|(_))')
    def litteral():     return [ident, variable, text, number]

    # maths
    def operator():     return list('+-/*\\') + ['**']
    def binop():        return [mathexp, ('(', mathexp, ')')], operator, [mathexp, ('(', mathexp, ')')]
    def mathexp():      return [number, binop]
    def assignment():   return variable, '=', mathexp

    # second level constructions
    def arg():          return [term, litteral, mathexp]
    def args():         return arg, ap.ZeroOrMore(',', arg)
    def multargs():     return args, ap.ZeroOrMore(';', args)

    # heads constructions
    def unnamedterm():  return '(', multargs, ')'
    def namedterm():    return ident, ap.Optional('(', multargs, ')')
    def term():         return [unnamedterm, namedterm]
    def selection():    return ap.Optional(number), '{', ap.OneOrMore(expression), '}', ap.Optional(number)

    # body constructions
    def not_term():     return 'not', namedterm
    def forall():       return namedterm, ':', term, ap.ZeroOrMore(',', term)
    def not_forall():   return 'not', namedterm, ':', term, ap.ZeroOrMore(',', term)
    def expression():   return [not_forall, forall, not_term, term, assignment]

    # program level constructions
    def body():         return expression, ap.ZeroOrMore(';', expression)
    def head():         return [selection, namedterm, (namedterm, ap.OneOrMore(';', namedterm))]
    def fact():         return head
    def constraint():   return ':-', body
    def rule():         return head, ':-', body
    def program():      return ap.OneOrMore([constraint, rule, fact], '.')

    return program
