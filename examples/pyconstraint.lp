% Test for extended propagators interface with Constraint and Main.


#script(python)


from clyngor import Constraint, Variable as V, Main

# Build the constraint on atom b
def formula(inputs) -> bool:
    return not inputs[('b', (2,))]

constraint = Constraint(formula, {('b', (V,))})

# regular main function
main = Main(constraint)

#end.


1{b(X): X=1..3}1.
