

from clyngor.asp_parsing import parse_asp_program, CodeAsTuple


def test_selection():
    ASP_CODE = r"""
    1 { sel(X): obj(X) } 1.
    { con(X,Y): obj(X), att(Y, 2) }.
    2 { sel(X): obj(X) } 4:- anatom.
    """
    rules = tuple(parse_asp_program(ASP_CODE, do=CodeAsTuple()))
    assert len(rules) == 3

    first, second, third = rules

    print('FIRST:', first)
    expected = ('selection', 1, 1, (('forall', 'sel', ('X',), (('term', 'obj', ('X',)),)),), ())
    print('EXPEC:', expected)
    assert first == expected

    print('SECOD:', second)
    expected = ('selection', 0, None, (('forall', 'con', ('X', 'Y'),
                                        (('term', 'obj', ('X',)),
                                         ('term', 'att', ('Y', 2)),),
                                        ),), ())
    print('EXPEC:', expected)
    assert second == expected

    print('THIRD:', third)
    expected = ('selection', 2, 4, (('forall', 'sel', ('X',),
                                     (('term', 'obj', ('X',)),),
                                     ),), (('term', 'anatom', ()),))
    print('EXPEC:', expected)
    assert third == expected


def test_multiple_rules():
    ASP_CODE = r"""
    a.
    b("les amis, \"coucou\".").
    obj(X):- rel(X,_) ; rel(X,Y): att(Y).
    att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
    """

    rules = tuple(parse_asp_program(ASP_CODE))
    assert len(rules) == 4

    first, second, third, fourth = rules
    assert first == ('term', 'a', ())

    print('SECOND:', second)
    assert second == ('term', 'b', (('text', r'les amis, \"coucou\".'),))

    print('THIRD:', third)
    expected = ('rule', 'obj', ('X',), (
        ('term', 'rel', ('X', '_')),
        ('forall', 'rel', ('X', 'Y'), (('term', 'att', ('Y',)),)),
    ))
    print('EXPEC:', expected)
    assert third == expected

    print('FOURTH:', fourth)
    expected = ('rule', 'att', ('Y',), (
        ('term', 'rel', ('_', 'Y')),
        ('forall', 'rel', ('X', 'Y'), (('term', 'obj', ('X',)),)),
    ))
    print('EXPECT:', expected)
    assert fourth == expected