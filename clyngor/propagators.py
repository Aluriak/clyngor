"""Definitions for propagators API of clyngor.

Exposes Main, Constraint and Variable.

"""

import math
from collections import defaultdict
from .utils import clingo_value_to_python


def Main(propagators:iter or object=(), groundable:iter or dict={'base': ()}):
    """Main function builder for clingo.

    Allow user to use:

        from clyngor import Main
        main = Main()

    instead of rewriting the standard main function:

        def main(prg):
            prg.ground([('base', [])])
            prg.solve()

    Also, Main() will add to the function additional treatments based on:

    propagators -- propagators instances to register (default none)
    groundable -- programs with their args to ground (default base without param)

    """
    if not isinstance(propagators, (tuple, list, set, frozenset)) or isinstance(propagators, Propagator):
        propagators = (propagators,)
    groundable = list(
        (prg, list(args)) for prg, args
        in (groundable.items() if isinstance(groundable, dict) else groundable)
    )
    def main(prg):
        for propagator in propagators:
            prg.register_propagator(propagator)
        prg.ground(groundable)
        prg.solve()
    return main


# Placeholder value for 'any value' in input atoms of Constraint's formulas.
Variable = Ellipsis


class Propagator:
    """Base class for high level propagator."""


    @staticmethod
    def run_with(filenames:[str]=(), inline:str='', programs:iter=(['base', ()],),
                 options:list=[]):
        import clingo
        ctl = clingo.Control(options)
        main = Main(propagators=self, groundable=programs)
        return main(ctl)


class Constraint(Propagator):
    """Base class for a particular class of user defined propagators.

    Instances of PyConstraint are valid propagators.
    The basic use is to provides the constructor with a callable
    and the set of atoms to watch and pass to the said callable.

    >>> Constraint(lambda ins: ins['q'], inputs={'q'})  #doctest: +ELLIPSIS
    <clyngor.propagators.Constraint object at ...>

    """

    def __init__(self, formula:callable, inputs:[tuple]):
        super().__init__()
        self.__inputs = frozenset(inputs)
        self.__str_inputs = frozenset(input for input in self.__inputs
                                      if isinstance(input, str))
        self.__raw_inputs = frozenset(input for input in self.__inputs
                                      if not isinstance(input, str))
        self.__formula = formula


    def init(self, init):
        self.__symbols = defaultdict(set)
        for atom in init.symbolic_atoms:
            lit = init.solver_literal(atom.literal)
            repr = atom.symbol.name, tuple(map(clingo_value_to_python, atom.symbol.arguments))
            repr_str = str(atom.symbol)
            if self._match_str(repr_str):
                init.add_watch(lit)
                self.__symbols[lit].add(repr_str)
            if self._match_raw(*repr):
                init.add_watch(lit)
                self.__symbols[lit].add(repr)
        self.__added_lit = None  # literal to be added to avoid yield of model


    def check(self, ctl):
        value_of = ctl.assignment.value
        checked = self.__formula({
            repr: value_of(lit)
            for lit, reprs in self.__symbols.items()
            for repr in reprs
        })
        if not self.__added_lit:
            self.__added_lit = ctl.add_literal()
            if not ctl.add_clause([self.__added_lit]) or not ctl.propagate():
                return
        if not checked:
            if not ctl.add_nogood([self.__added_lit]) or not ctl.propagate():
                return


    def _match_str(self, atom:str) -> bool:
        """True if given string atom is in inputs"""
        if atom in self.__str_inputs:
            return True

    def _match_raw(self, name:str, args:tuple) -> bool:
        """True if given atom is in inputs"""
        if (name, args) in self.__raw_inputs:
            return True
        # more complex verification: it may be because of variables
        for pred, params in self.__raw_inputs:
            if pred == name and len(args) == len(params):
                for arg, param in zip(args, params):
                    if param is Variable or arg == param:
                        return True
