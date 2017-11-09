"""Routines to manipulate ASP source code as a graph.

The following data structure are used here.

Dependancy graph -- mapping {rule: {dependancies}} where keys are rules
                    and values are iterable of rules yielding atoms used by key.
atoms endpoints -- tuple (source, target) where source and target are mappings
                   of atoms to the rules that use them, or the rules
                   that yield them, respectively.
program -- a tuple representation of an ASP source code, as parsed by
           asp_parsing.parser module using CodeAsTuple visitor.
           In this representation, rules should be ordered, or the indexes
           of other data structures may be wrong.

Note that atoms are identified by their predicate.
This behavior may change in the future to include arity (number of parameter),
which is much more accurate.

"""
import itertools
from collections import defaultdict
from clyngor.asp_parsing.precise_parser import parse_asp_program, CodeAsTuple


def program_to_endpoints(program:str or tuple, node_as_index:bool=True) -> (dict, dict):
    """Return the atoms endpoints computed from given parsed ASP program.

    program -- either a source code as string or a parsed one
    node_as_index -- return nodes as index of rules in the source code
                     instead of rules themselves
    return ({pred: {succ}}, {succ: {pred}})

    """
    if isinstance(program, str):
        program = tuple(parse_asp_program(program, do=CodeAsTuple()))
    atom_source = defaultdict(set)  # predicate -> rules using it
    atom_target = defaultdict(set)  # predicate -> rules yielding it

    # explore the full structure to populate sources and targets
    for idx, (type, *data) in enumerate(program):
        if type == 'rule':
            head, body = data
            atom_target[head[1]].add(idx)
            for (subtype, *subdata) in body:
                if subtype in {'term', '¬term'}:
                    atom_source[subdata[0]].add(idx)
                elif subtype in {'forall', '¬forall'}:
                    atom_source[subdata[0]].add(idx)
                    for (subsubtype, *subsubdata) in subdata[2]:
                        if subsubtype == 'term':
                            atom_source[subsubdata[0]].add(idx)
                        else:
                            assert False, "Type {} is unexpected in forall body".format(subtype)
                else:
                    assert False, "Type {} is unexpected in rule body".format(subtype)

        elif type == 'term':
            atom_target[data[0]].add(idx)
        elif type == 'selection':
            for (subtype, *subdata) in data[2]:
                if subtype in {'term', '¬term', 'forall', '¬forall'}:
                    atom_target[subdata[0]].add(idx)
                else:
                    assert False, "Type {} is unexpected in selection".format(subtype)
        elif type == 'constraint':
            for (subtype, *subdata) in data[0]:
                if subtype in {'term', '¬term', 'forall', '¬forall'}:
                    atom_source[subdata[0]].add(idx)
                else:
                    assert False, "Type {} is unexpected in selection".format(subtype)
        else:
            assert False, "Type {} is unexpected at first level".format(type)

    if node_as_index:
        return dict(atom_source), dict(atom_target)
    else:  # use the parsed rules themselves
        return tuple(
            {program[pred]: frozenset(program[succ] for succ in succs)
             for pred, succs in graph.items()}
            for graph in (atom_source, atom_target)
        )


def atoms_endpoints_to_dependancy_graph(atom_source:dict, atom_target:dict) -> dict:
    """Return the dependancy graph

    atom_source -- {atom: {rule using atom}}
    atom_target -- {atom: {rule yielding atom}}

    """
    graph = defaultdict(set)
    for predicate in set(atom_source.keys()) | set(atom_target.keys()):
        for source, target in itertools.product(atom_source.get(predicate, ()), atom_target.get(predicate, ())):
            graph[source].add(target)
    return dict(graph)


def program_to_dependancy_graph(program:str or tuple,
                                node_as_index:bool=True,
                                have_comments:bool=True) -> dict:
    """Most high level function: compute dependancy graph from the source code
    directly"""
    if isinstance(program, str):
        program = tuple(parse_asp_program(program, do=CodeAsTuple(), have_comments=have_comments))
    endpoints = program_to_endpoints(program, node_as_index)
    return atoms_endpoints_to_dependancy_graph(*endpoints)
