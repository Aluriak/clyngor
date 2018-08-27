"""Definitions for propagators API of clyngor.

Exposes Main, Constraint and Variable.

"""

import os
import math
import tempfile
from collections import defaultdict
from . import utils
from .answers import ClingoAnswers


def Main(files:iter=(), inline:str='', nb_model:int=0,
         propagators:iter or object=(), observers:iter or object=(),
         programs:iter or dict={'base': ()}, generator:bool=False):
    """Main function builder for clingo.

    Allow user to use:

        from clyngor import Main
        main = Main()

    instead of rewriting the standard main function:

        def main(prg):
            prg.ground([('base', [])])
            return prg.solve()

    Also, Main() will add to the function additional treatments based on:

    propagators -- propagators instances to register (default none)
    observers -- observers instances to register (default none)
    programs -- programs with their args to ground (default base without param)
    files -- list of files to ground
    inline -- ASP code to add to base program
    generator -- the main function will return a ClingoAnswers instance instead
                 of returning the solve call result
    nb_model -- number of model to search for. 0 stands for all.

    """
    if not isinstance(propagators, (tuple, list, set, frozenset)):
        propagators = (propagators,)
    if not isinstance(observers, (tuple, list, set, frozenset)):
        observers = (observers,)

    programs = list(
        (prg, list(args)) for prg, args
        in (programs.items() if isinstance(programs, dict) else programs)
    )
    if inline:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as fd:
            fd.write(inline)
            tempfile_to_del = fd.name
            files = tuple(files) + (tempfile_to_del,)
            assert files, fd.name

    def main(prg):
        for file in files:
            prg.load(file)
        if inline and tempfile_to_del:  # remove the tempfile after the work.
            os.remove(tempfile_to_del)
        for observer in observers:
            prg.register_observer(observer)
        for propagator in propagators:
            prg.register_propagator(propagator)
        prg.ground(programs)
        prg.configuration.solve.models = nb_model
        if generator:
            return ClingoAnswers(prg)
        prg.solve()
    return main


# Placeholder value for 'any value' in input atoms of Constraint's formulas.
Variable = Ellipsis


class Propagator:
    """Base class for high level propagator."""

    def __init__(self, follow:iter or str=()):
        """
        follow -- iterable or string describing the atoms to follow during solving
        """
        self._followeds = frozenset(utils.make_hashable(follow))
        self._str_followeds = frozenset(fol for fol in self._followeds
                                        if isinstance(fol, str))
        self._raw_followeds = frozenset(fol for fol in self._followeds
                                        if not isinstance(fol, str))


    def init(self, init):
        self.symbols = defaultdict(set)
        if not self._followeds: return
        for atom in init.symbolic_atoms:
            lit = init.solver_literal(atom.literal)
            repr_str = str(atom.symbol)
            if self._match_str(repr_str):
                init.add_watch(lit)
                self.symbols[lit].add(repr_str)
            else:  # not in string inputs, maybe in raws ?
                repr = atom.symbol.name, tuple(map(utils.clingo_value_to_python,
                                                   atom.symbol.arguments))
                if self._match_raw(*repr):
                    init.add_watch(lit)
                    self.symbols[lit].add(repr)


    def propagate(self, ctl, changes):
        value_of = ctl.assignment.value
        values = {
            repr: value_of(lit)
            for lit, reprs in self.symbols.items()
            for repr in reprs
        }
        complete = all(value is not None for value in values.values())
        partial = any(value is not None for value in values.values())
        if complete and hasattr(self, 'on_all_input'):
            discard = self.on_all_input(values)
        elif partial and hasattr(self, 'on_any_input'):
            discard = self.on_any_input(values)
        else:
            return

        # object may have invalidated the model
        if discard:
            self.__discard_model(ctl)

    def __discard_model(self, ctl):
        """Make the current model false by adding a clause
        """
        one_literal = ctl.add_literal()
        # make it true, then false.
        if not ctl.add_clause([one_literal]) or not ctl.propagate():
            return
        if not ctl.add_nogood([one_literal]) or not ctl.propagate():
            return

    def check(self, ctl):
        return self.propagate(ctl, [])


    def _match_str(self, atom:str) -> bool:
        """True if given string atom is in inputs"""
        if atom in self._str_followeds:
            return True

    def _match_raw(self, name:str, args:tuple) -> bool:
        """True if given atom is in inputs"""
        if (name, args) in self._raw_followeds or (name,) in self._raw_followeds:
            return True
        # more complex verification: it may be because of variables
        for atom in self._raw_followeds:
            if len(atom) != 2: continue
            pred, params = atom
            if pred == name and len(args) == len(params):
                for arg, param in zip(args, params):
                    if param is Variable or arg == param:
                        return True


    def run_with(self, filenames:[str]=(), inline:str='',
                 programs:iter=(['base', ()],), options:list=[]):
        import clingo
        ctl = clingo.Control(options)
        main = Main(propagators=self, programs=programs, inline=inline, generator=True)
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
        super().__init__(follow=inputs)
        self.__formula = formula

    def on_all_input(self, values:dict):
        return self.__formula(values)

    # def on_all_inputs(self):
        # pass


