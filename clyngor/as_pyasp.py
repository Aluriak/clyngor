"""The following definitions are here to provides to end-user
a pyasp-like interface, facilitating migrations towards it.

"""


class Atom:
    """Keep an interface close to pyasp"""

    def __init__(self, predicate:str, args:iter):
        self.predicate = predicate
        self._args = tuple(args)

    def args(self): return self._args

    def __str__(self): return '{}({})'.format(self.predicate, self.args())
    def __repr__(self): return str(self)
