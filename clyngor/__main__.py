
from timeit import timeit
from pprint import pprint
from functools import partial

from clyngor import ASP
from clyngor import asp_parsing
from clyngor.asp_parsing import alt_parse


ASP_CODE = """
rel(a,c). rel(a,d). rel(b,d). rel(b,e).
obj(X):- rel(X,_) ; rel(X,Y): att(Y).
att(Y):- rel(_,Y) ; rel(X,Y): obj(X).
%* w.
- coucou
*%
:- not obj(X):obj(X).
:- not att(Y):att(Y).
"""

def time_efficiency(parser:callable, number:int=1000) -> float:
    def run():
        return asp_parsing.program_to_dependancy_graph(parser(ASP_CODE))
    return 'Perform 1000 graphs in {} seconds.'.format(timeit(run, number=number))

def time_efficiency_alt():
    program = (ASP_CODE)
    func = partial(asp_parsing.program_to_dependancy_graph, program, have_comments=False)
    return 'Perform 1000 graphs in ' + str(timeit(func, number=1000)) + ' seconds.'
    # last time: 0.01s


if __name__ == '__main__':
    answers = ASP(ASP_CODE)
    for answer in answers.by_predicate.first_arg_only:
        print('{' + ','.join(answer['obj']) + '} × {' + ','.join(answer['att']) + '}')
    print()

    print('Dependancy graph:')
    pprint(asp_parsing.program_to_dependancy_graph(ASP_CODE))
    print()

    print('Benchmark:')
    for parser in (asp_parsing.precise_parser.parse_asp_program_by_arpeggio,  # last time: 4.0s, 5.8s
                   asp_parsing.precise_parser.parse_asp_program_by_pypeg):  # last time: 8.5s, 9.5s
        print(parser.__name__.ljust(17) + ':', time_efficiency(parser))
    print()


    print('ALTERNATIVE:')
    program = alt_parse.parse_asp(ASP_CODE)
    print(asp_parsing.program_to_dependancy_graph(program))


    print('PRETTY PRINTING:')
    from pprint import pprint
    program = asp_parsing.parse_asp_program(ASP_CODE)
    pprint(program)
    print('\n'.join(asp_parsing.pprint.to_asp_source_code(program)))
