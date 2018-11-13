% Show that the python constraint is non-working.
% This example shows that the model are not correctly discarded
%  by Constraint object. This is (at last) because of propagators API,
%  that does not support fully what we need (model invalidation).
%
%  Some ressources for future solving of that feature-killer issue:
%  - what we want is not possible. By design.
%      https://sourceforge.net/p/potassco/mailman/message/36358095/
%  - some other peoples wants it, the solution seems to be external atoms
%      https://sourceforge.net/p/potassco/mailman/message/35480361/
%  - but external atoms are not handlable during solving through propagator API
%      https://potassco.org/clingo/python-api/current/clingo.html#PropagateControl
%  - cool find with propagators:
%      https://twitter.com/rndmcnlly/status/867605489789489152
%
% See clyngor/test/test_propagator_class.py:test_pyconstraint_recursion_problem
%  for a living example of that issue.

#script(python)
from clyngor import Constraint, Variable as V, Main
def formula(inputs):  return inputs['p', (2,)]
constraint = Constraint(formula, {('p', (V,))})
main = Main(propagators=constraint)
#end.
{p(1..3)}.  % powerset of p(X).
