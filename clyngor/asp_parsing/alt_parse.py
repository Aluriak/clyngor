

import re
import itertools
import pypeg2 as pg


def parse_asp(source_code:str) -> tuple:
    return tuple(parsed_to_tuple(pg.parse(text=source_code, thing=Program, comment=comment_asp)))

def parsed_to_tuple(program) -> tuple:
    return program.as_tuple()



comment_asp = [re.compile(r'%\*.*\*%', flags=re.DOTALL), re.compile('%.*')]

Ident = re.compile(r'[a-z][a-zA-Z0-9_]*')
Variable = re.compile(r'(([A-Z][a-zA-Z0-9_]*)|(_))')


def to_tuple(x):
    return x.as_tuple() if hasattr(x, 'as_tuple') else x


class List(pg.List):
    """A pypeg2 list exposing a basic transformation routine"""
    flat = False

    def as_tuple(self):
        if type(self).flat:
            return tuple(itertools.chain.from_iterable(map(to_tuple, self)))
        else:
            return tuple(map(to_tuple, self))

class Number(List):
    grammar = re.compile(r'-?[0-9]+')
    def as_tuple(self):
        assert len(self) == 1
        return int(tuple(self)[0])

class Text(List):
    grammar = '"', re.compile(r'((\\")|([^"]))*'), '"'
    def as_tuple(self):
        assert len(self) == 1
        return ('text', tuple(self)[0])

class Litteral(List):
    grammar = [Number, Ident, Text, Variable]
    def as_tuple(self):
        assert len(self) == 1
        return to_tuple(tuple(self)[0])

class Arg(List):
    grammar = Litteral  # updated later
    def as_tuple(self):
        assert len(self) == 1
        return tuple(self)[0].as_tuple()
class Args(List):
    grammar = Arg, pg.maybe_some(',', Arg)
class MultArgs(List):
    grammar = Args, pg.maybe_some(';', Args)
    def as_tuple(self):
        if len(self) > 1:
            return ('disjunction', *tuple(map(to_tuple, self)))
        return tuple(map(to_tuple, tuple(self)[0]))

class UnamedTerm(List):
    grammar = '(', MultArgs, ')'
    def as_tuple(self):
        assert len(self) == 1
        children = tuple(self)[0].as_tuple()
        if children[0] == 'disjunction':
            return children
        return ('term', *children)
class NamedTerm(List):
    grammar =  Ident, pg.optional('(', MultArgs, ')')
    def as_tuple(self):
        children = tuple(self)
        assert len(children) in {1, 2}
        if len(children) == 1:
            return ('term', to_tuple(children[0]), ())
        return ('term', *map(to_tuple, children))
class Term(List):
    grammar = [UnamedTerm, NamedTerm]
    flat = True
Arg.grammar = [Term, Litteral]


# body constructions
class NotTerm(List):
    grammar = 'not', NamedTerm
    def as_tuple(self):
        type, pred, args = tuple(self)[0].as_tuple()
        assert type == 'term'
        return '¬' + type, pred, args
class ForAll(List):
    grammar = NamedTerm, ':', Term, pg.maybe_some(',', Term)
    def as_tuple(self):
        head, *conditions = self
        head = head.as_tuple()[1:]  # only the predicate and args
        conditions = tuple(sub.as_tuple() for sub in conditions)
        return ('forall', *head, conditions)
class NotForAll(List):
    grammar = 'not', ForAll
    def as_tuple(self):
        type, pred, args, conditions = tuple(self)[0].as_tuple()
        assert type == 'forall'
        return '¬' + type, pred, args, conditions
class Expression(List):
    grammar = [NotForAll, ForAll, NotTerm, Term]
    flat = True

class Selection(List):
    grammar = pg.optional(Number), '{', pg.some(Expression), '}', pg.optional(Number)
    def as_tuple(self):
        children = tuple(map(to_tuple, self))
        down, up, exprs = 0, None, ()
        assert len(children) in {1, 2, 3}
        print('CHILDS:', children)
        if isinstance(children[0], int):
            down = children[0]
        if isinstance(children[-1], int):
            up = children[-1]
        if up and down:
            assert len(children) == 3
            exprs = children[1]
        elif up:
            assert len(children) == 2
            exprs = children[0]
        elif down:
            assert len(children) == 2
            exprs = children[1]
        else:
            assert len(children) == 1
            exprs = children[0]

        return 'selection', down, up, (exprs,)


class Body(List):
    grammar = Expression, pg.maybe_some(';', Expression)
    def as_tuple(self):
        return tuple(sub.as_tuple() for sub in self)

class Head(List):
    grammar = [Selection, NamedTerm, (NamedTerm, pg.some(';', NamedTerm))]
    def as_tuple(self):
        assert len(self) == 1
        body = self[0]
        if ';' in body:
            return 'disjunction', body.as_tuple()
        return body.as_tuple()

class Constraint(List):
    grammar = ':-', Body
    def as_tuple(self):
        assert len(self) == 1
        body = self[0]
        return 'constraint', body.as_tuple()

class Rule(List):
    grammar = Head, ':-', Body
    def as_tuple(self):
        head, body = self
        return 'rule', head.as_tuple(), body.as_tuple()

class Program(List):
    grammar = pg.some([Constraint, Rule, Head], '.')
