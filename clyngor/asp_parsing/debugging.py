"""Routines implementing debugging help.

"""

from clyngor import asp_parsing
from clyngor.asp_parsing import precise_parser
from clyngor.asp_parsing import byline_parser



def lines_for(rule:tuple or str, id:int or str=1) -> tuple:
    """Return the parsed construction of debug lines debugging given rule"""
    if isinstance(rule, str):
        rule = tuple(precise_parser.parse_asp_program(rule))[0]
    print('RULE:', rule)
    head = rule[1]
    body = rule[2]
    assert len(body) > 0, "empty body"
    assert rule[0] == 'rule', "input data must a rule"
    assert len(rule[1]) == 3
    assert head[0] == 'term', "head must be a term"
    ruleid = str(id)
    print('ID:', ruleid)
    head = ('term', 'head', (ruleid,))
    conditions = tuple(term for term in body if not term[0].startswith('¬'))
    constraints = tuple(term for term in body if term[0].startswith('¬'))
    print('CONDITIONS:', conditions)
    print('CONSTRAINTS:', constraints)
    not_conditions = tuple(('¬' + type, *data) for type, *data in conditions)
    not_constraints = tuple(('not', constraint) for constraint in constraints)
    ok = (('term', 'ok', (ruleid,)),)
    return (
        ok[0],
        ('rule', ('term', 'head', (ruleid,)), (('term', 'ap', (ruleid,)),
                                               ('¬term', 'ko', (ruleid,)))),
        ('rule', ('term', 'ap', (ruleid,)), ok + conditions + constraints),
        ('rule', ('term', 'bl', (ruleid,)), ok + not_conditions),
        ('rule', ('term', 'bl', (ruleid,)), ok + not_constraints),
    )
