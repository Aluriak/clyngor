
from clyngor import asp_parsing


def test_debug_lines():
    rule = ('rule', ('term', 'a', ('X',)), (
        ('term', 'b', ('X',)),
        ('¬term', 'c', ('X',)),
    ))
    lines = asp_parsing.debug.lines_for(rule, id=1)
    print(lines)
    assert lines == (
        ('term', 'ok', ('1',)),
        ('rule',
         ('term', 'head', ('1',)),
         (('term', 'ap', ('1',)), ('¬term', 'ko', ('1',)))),
        ('rule',
         ('term', 'ap', ('1',)),
         (('term', 'ok', ('1',)), ('term', 'b', ('X',)), ('¬term', 'c', ('X',)))),
        ('rule',
         ('term', 'bl', ('1',)),
         (('term', 'ok', ('1',)), ('¬term', 'b', ('X',)))),
        ('rule',
         ('term', 'bl', ('1',)),
         (('term', 'ok', ('1',)), ('not', ('¬term', 'c', ('X',)))))
    )


