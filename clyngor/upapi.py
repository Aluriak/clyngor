"""Decorators and functions for python embedded ASP source code.


"""

import math
import inspect
from functools import wraps, partial


def _converted_types(ignore_bad_type:bool=True):
    """Decorator for functions accessed by ASP, using type annotations to
    convert input types in their expected type.

    Also, if the decorated function is a generator, it will be transformed into a
    list in order to match clingo's API.
    Non-conformant types are sent to the function without modification.

    ignore_bad_type -- Non-conformant types are ignored.

    """
    def convert_value(val:object, annot:object) -> object:
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
        else:
            if ignore_bad_type:
                raise TypeError("Bad type hint match from ASP")
            else:
                return val

    def convert_args(argspec, args, kwargs) -> (str, object):
        for name, arg in zip(argspec.args, args):
            annot = argspec.annotations.get(name)
            yield name, convert_value(arg, annot)
        for name, arg in kwargs.items():
            annot = argspec.annotations.get(name)
            yield name, convert_value(arg, annot)

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
                return return_type(ret)
            elif isgenerator:
                return list(ret)
            return ret

        return decorated
    return decorator


converted_types = _converted_types(True)
converted_types_or_symbols = _converted_types(False)
