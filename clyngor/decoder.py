"""Definition of the Decoder helpers, allowing one to define and use decoders.

A decoder is an object that will be created
when the required atoms are found in the ASP model.

It is heavily inspired from JSON decoders.

"""
from itertools import product
from functools import lru_cache
from inspect import signature
from clyngor import solve


def decode(*args, decoders:iter, **kwargs):
    """Yield objects built from decoders from all models.

    Expects same (kw)args as clyngor.solve, but decoders MUST be provided.

    """
    decoders = tuple(decoders)
    for model in solve(*args, **kwargs).by_predicate:
        for decoder in decoders:
            yield from objects_from_model(decoder, model)

def objects_from_model(decoder:type, model:dict):
    """Yield objects described by given decoder when applied to given model."""
    atoms_group = object_builder_from_decoder(decoder)
    unique_atoms_iterable = tuple(tuple(model.get(atom_name, ())) for atom_name in atoms_group['foreach'])
    all_atoms_iterable = tuple(tuple(model.get(atom_name, ())) for atom_name in atoms_group['all'])
    for unique_atoms in product(*unique_atoms_iterable):
        unique_atoms_args = dict(zip(atoms_group['foreach'], unique_atoms))
        all_atoms_args = dict(zip(atoms_group['all'], all_atoms_iterable))
        yield decoder(**unique_atoms_args, **all_atoms_args)

@lru_cache(maxsize=32)
def object_builder_from_decoder(decoder:type) -> dict:
    if not hasattr(decoder, '__init__'):
        raise ValueError(f"Decoder {decoder} has no __init__ method")
    constructor = decoder.__init__
    sig = signature(constructor)
    params = iter(sig.parameters.items())
    _ = next(params)  # ignore the self param
    atoms_all, atoms_each = set(), set()
    for name, param in params:
        anno = param.annotation
        if anno is all:  # let's collect all these objects
            atoms_all.add(name)
        elif anno == 1:  # one for each atom
            atoms_each.add(name)
        else:
            raise ValueError(f"Decoder can't handle the annotation '{anno}'")
    return {
        'all': frozenset(atoms_all),
        'foreach': frozenset(atoms_each),
    }
