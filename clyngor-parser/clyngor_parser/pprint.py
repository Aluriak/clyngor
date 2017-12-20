"""Routines for printings of parsed ASP programs.

"""


class BaseVisitor:
    """Base class for user-defined visitor over ASP source code"""

    def term(self, predicate:str, args:iter, not_:bool):
        raise NotImplementedError()

    def forall(self, predicate:str, args:iter, conditions:iter, not_:bool):
        raise NotImplementedError()

    def selection(self, down:int, up:int, generateds:iter):
        raise NotImplementedError()

    def rule(self, head:'term', body:iter):
        raise NotImplementedError()

    def multirule(self, head:iter, body:iter):
        raise NotImplementedError()

    def constraint(self, body:iter):
        raise NotImplementedError()

    def disjunction(self, items:iter):
        raise NotImplementedError()

    def litteral(self, item:str or int):
        raise NotImplementedError()

    def program(self, rules:iter):
        raise NotImplementedError()

    @classmethod
    def walk_on(cls, program:tuple, **kwargs):
        """Return the visitor results of its walk on given program"""
        visitor = cls(**kwargs)
        return tuple(map(visitor.visite, program))

    def visite(self, obj):
        type = obj[0]
        if type == 'rule':
            assert len(obj) == 3
            head, body = obj[1:]
            return self.visite(head) + rule_marker + body_sep.join(map(self.visite, body))
        if type == 'multirule':
            head, body = obj[1:]
            assert len(obj) == 3
            head = map(self.visite, head)
            body = map(self.visite, body)
            return disjunction_sep.join(head) + rule_marker + body_sep.join(body)
        if type == 'constraint':
            assert len(obj) == 2
            body = map(self.visite, obj[1])
            return rule_marker + body_sep.join(body)
        if type in {'term', '¬term'}:
            name, args = obj[1:]
            args = map(self.visite, args)
            not_ = ('not ' if type.startswith('¬') else '')
            return not_ + str_term(name, args)
        if type in {'forall', '¬forall'}:
            assert len(obj) == 4
            name, args, conditions = obj[1:]
            not_ = ('not ' if type.startswith('¬') else '')
            return not_ + str_term(name, map(self.visite, args)) + ':' + conditions_sep.join(map(self.visite, conditions))
        if type == 'disjunction':
            raise NotImplementedError()
        if type in 'selection':
            assert len(obj) == 4
            down, up, generateds = obj[1:]
            return str_selection(down, up, map(self.visite, generateds))
        # now here, it is a litteral
        return args_sep.join(map(str, obj))




def to_asp_source_code(program:tuple, rule_marker:str=':- ', body_sep:str=' ; ',
                       conditions_sep:str=', ', args_sep:str=',',
                       disjunction_sep:str=';', rule_end:str='.',
                       selection_always_show_numbers:bool=False) -> iter:
    """Yield a ASP compliant string implementing each rule in program.

    """
    assert isinstance(program, tuple)
    def str_term(pred, args:iter) -> str:
        args = tuple(args)
        return '{}({})'.format(pred, args_sep.join(args)) if args else pred
    def str_selection(down:int, up:int, conditions:iter) -> str:
        out = ''
        if selection_always_show_numbers or down != 0:
            out += str(down) + ' '
        out += '{ ' + ';'.join(conditions) + ' }'
        if selection_always_show_numbers or up != None:
            out += ' ' + str(up)
        return out
    def str_disjunction(args:iter) -> str:
        return disjunction_sep.join(args)


    def stringifier(obj) -> callable:
        if isinstance(obj, int):  return str(obj)
        type = obj[0]
        if type == 'rule':
            assert len(obj) == 3
            head, body = obj[1:]
            return stringifier(head) + rule_marker + body_sep.join(map(stringifier, body))
        if type == 'multirule':
            head, body = obj[1:]
            assert len(obj) == 3
            head = map(stringifier, head)
            body = map(stringifier, body)
            return disjunction_sep.join(head) + rule_marker + body_sep.join(body)
        if type == 'constraint':
            assert len(obj) == 2
            body = map(stringifier, obj[1])
            return rule_marker + body_sep.join(body)
        if type in {'term', '¬term'}:
            name, args = obj[1:]
            args = map(stringifier, args)
            not_ = ('not ' if type.startswith('¬') else '')
            return not_ + str_term(name, args)
        if type in {'forall', '¬forall'}:
            assert len(obj) == 4
            name, args, conditions = obj[1:]
            not_ = ('not ' if type.startswith('¬') else '')
            return not_ + str_term(name, map(stringifier, args)) + ': ' + conditions_sep.join(map(stringifier, conditions))
        if type == 'disjunction':
            raise NotImplementedError()
        if type == 'not':
            assert len(obj) == 2
            return 'not ' + stringifier(obj[1])
        if type == 'selection':
            assert len(obj) == 4
            down, up, generateds = obj[1:]
            return str_selection(down, up, map(stringifier, generateds))
        # now here, it is a litteral
        if isinstance(obj, (str, int)):
            return str(obj)
        return args_sep.join(map(str, obj))

    for rule in program:
        yield stringifier(rule) + rule_end

parsed_to_source = to_asp_source_code


def to_human_text(program:tuple) -> str:
    """Return describing the program for humans.

    """
