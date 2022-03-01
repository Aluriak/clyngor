"""Decorators and functions for python embedded ASP source code.


"""

import math
import inspect
import clyngor
from functools import wraps


def _converted_types(ignore_bad_type:bool=True):
    """Decorator for functions accessed by ASP, using type annotations to
    convert input types in their expected type.

    Also, if the decorated function is a generator, it will be transformed into a
    list in order to match clingo's API.
    Non-conformant types are sent to the function without modification.

    ignore_bad_type -- Non-conformant types are ignored.

    """
    if not clyngor.have_python_support() or not clyngor.clingo_module_available:
        return clyngor.utils.null_decorator
    from clingo import symbol
    def clingo_to_python(val:symbol, annot:type) -> object:
        if annot is None or not type(val).__name__ == 'Symbol':
            return val
        elif annot is str and val.type == val.type.String:
            return val.string
        elif annot is int and val.type == val.type.Number:
            return val.number
        elif annot is int and val.type == val.type.Infimum:
            return -math.inf
        elif annot is int and val.type == val.type.Supremum:
            return math.inf
        elif ignore_bad_type:
            raise TypeError(f"Bad type hint match from ASP: received {type(val)}, annotation is {annot}")
        else:
            return val

    def output_to_clingo(val: object) -> symbol:
        if isinstance(val, symbol.Symbol):
            return val
        elif isinstance(val, str):
            return symbol.String(val)
        elif isinstance(val, int):
            return symbol.Number(val)
        elif val == math.inf:
            return symbol.Infimum()
        elif val == -math.inf:
            return symbol.Supremum()
        elif isinstance(val, list):
            return list(map(output_to_clingo, val))
        elif isinstance(val, tuple):
            return symbol.Function('', tuple(map(output_to_clingo, val)))
        elif type(val).__name__ == 'generator':
            return output_to_clingo(list(val))
        elif ignore_bad_type:
            raise TypeError(f"Function outputed value {repr(val)} of type {type(val)}, which is not handled.")
        else:
            return val

    def convert_args(argspec, args, kwargs) -> (str, object):
        for name, arg in zip(argspec.args, args):
            annot = argspec.annotations.get(name)
            yield name, clingo_to_python(arg, annot)
        for name, arg in kwargs.items():
            annot = argspec.annotations.get(name)
            yield name, clingo_to_python(arg, annot)

    def decorator(func):
        argspec = inspect.getfullargspec(func)
        isgenerator = inspect.isgeneratorfunction(func)

        @wraps(func)
        def decorated(*args, **kwargs):
            try:
                ret = func(**dict(convert_args(argspec, args, kwargs)))
            except TypeError:
                return []  # nothing to be done
            return_type = argspec.annotations.get('return')
            if callable(return_type):
                ret = return_type(ret)
            elif isgenerator:
                ret = list(ret)  # each returned object is an independant value.
            ret = output_to_clingo(ret)
            return ret

        return decorated
    return decorator

converted_types = _converted_types(True)
converted_types_or_symbols = _converted_types(False)
