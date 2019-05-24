"""Showing how to ground a program, and later solve from the grounded representation"""

from clyngor import grounded_program, solve_from_grounded

grounded = grounded_program(inline='1{p(a;b;c)}1.')
print('GROUNDED:')
print(grounded)
print()
print('SOLVED:')
for idx, model in enumerate(solve_from_grounded(grounded).by_predicate):
    print(idx, model)
