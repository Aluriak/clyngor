"""The following definitions are here to provides to end-user
a pyasp-like interface, facilitating migrations towards it.

Note that all the interface is not available. Just the very basics.

"""

import tempfile
import itertools

class Atom:
    """Keep an interface close to pyasp"""

    def __init__(self, predicate:str, args:iter=()):
        self.predicate = predicate
        self.arguments = tuple(args)

    def args(self): return self.arguments

    def nb_args(self):
        return len(self.arguments)
    def arg(self, n):
        return self.arguments[n]

    def __eq__(self, other_atom)-> bool:
        return self.predicate == other_atom.predicate and self.arguments == other_atom.arguments

    def __hash__(self):
        return hash((self.predicate, self.arguments))

    def __str__(self):
        if self.nb_args() > 0:
            return '{}({})'.format(self.predicate, ','.join(map(str, self.arguments)))
        else:
            return self.predicate

    def __repr__(self): return str(self)

    def __iter__(self):
        """Conserve the same API as regular representation of atoms"""
        return iter((self.predicate, self.arguments))

    def from_tuple_repr(atom:tuple) -> object:
        "Expects something like ('a', (('b', ('c', 'd')))), encoding a(b(c,d))"
        def from_args(args:tuple) -> object:
            for arg in args:
                if isinstance(arg, (tuple, list)):
                    yield Atom.from_tuple_repr(arg)
                else:
                    yield arg
        pred, args = atom
        return Atom(pred, from_args(args))



# aliases used by pyasp
Term = Atom

class TermSet:
    """Collection of Term/Atom.

    Behave (about) like a set.

    """

    def __init__(self, terms:iter=()):
        self._terms = frozenset(terms)

    def __iter__(self):
        return iter(self._terms)

    def __len__(self):
        return sum(1 for term in self._terms)

    def __eq__(self, other):
        return set(self._terms) == other

    def add(self, atom:Atom):
        "Add given Atom to self"
        self._terms |= frozenset({atom})

    def union(self, *others:object) -> object:
        "Return a new TermSet containing all Atoms of self and each of others TermSet"
        return TermSet(itertools.chain(self._terms, *(other._terms for other in others)))

    def to_file(self, fname:str=None):
        """Return the filename in which term set have been written"""
        if not fname:
            with tempfile.NamedTemporaryFile('w', delete=False) as fd:
                fname = fd.name
        with open(fname, 'w') as fd:
            for term in self:
                fd.write(str(term) + '.\n')
        return fname

    def __str__(self):
        return '.'.join(map(str, self)) + ('.' if self._terms else '')

    def __repr__(self): return str(self)
