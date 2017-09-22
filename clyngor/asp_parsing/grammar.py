"""Definition of the ASP grammar"""


import arpeggio as ap


def asp_grammar():
    """Implement the Answer Set Programming grammar.

    """
    # litterals
    def ident():        return ap.RegExMatch(r'[a-z][a-zA-Z0-9_]*')
    def number():       return ap.RegExMatch(r'-?[0-9]+'),
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

    # metaprogramming
    def arityterm():    return ident, '/', ap.RegExMatch(r'[0-9]+')
    def meta_show():    return 'show', ap.Optional([forall, arityterm, term, litteral])
    def meta_const():   return 'const', ident, '=', litteral
    # def meta_max():   return 'const', ident, '=', litteral
    # def meta_min():   return 'const', ident, '=', litteral

    # program level constructions
    def body():         return expression, ap.ZeroOrMore(';', expression)
    def head():         return [selection, namedterm]
    def constraint():   return ':-', body
    def rule():         return head, ':-', body
    def multirule():    return (namedterm, ap.OneOrMore(';', namedterm)), ':-', body
    def meta():         return '#', [meta_show, meta_const]
    def program():      return ap.OneOrMore([meta, constraint, multirule, rule, head], '.')

    return program


def asp_grammar_comments():
    # return [ap.RegExMatch(r'%\*.*?\*%'), ap.RegExMatch(r'%.*$')]  # TODO: handle multiline comments
    # wait for Arpeggio's PR#38, which fix the problem
    # return [ap.RegExMatch(r'%\*.*?\*%', multiline=True), ap.RegExMatch(r'%.*$')]
    # Follows a non-efficient but working way to do multiline
    return [ap.RegExMatch(r'%\*((([^\*]?%)|([^%]?\*))|([^\*%]))*\*%'), ap.RegExMatch(r'%.*$')]
