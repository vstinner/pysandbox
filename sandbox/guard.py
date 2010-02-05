from inspect import getargs
from types import FunctionType

def _guard(getargs=getargs, len=len, enumerate=enumerate, type=type,
TypeError=TypeError, ValueError=ValueError):
    def guard(**spec):
        def decorator(original_func):
            if type(original_func) is not FunctionType:
                raise TypeError("Argument to the guard decorator is not a original_func.")

            func_args = getargs(original_func.func_code)[0]

            def func(*args, **kwargs):
                for i, param in enumerate(args):
                    req = spec[func_args[i]]
                    if type(param) is not req:
                        raise TypeError(
                            "%s has to be %r" % (func_args[i], req)
                            )
                for name, param in kwargs.iteritems():
                    if name not in spec:
                        raise ValueError("Unknown argument %s" % name)
                    req = spec[name]
                    if type(param) is not req:
                        raise TypeError("%s has to be %r" % (name, req))
                return original_func(*args, **kwargs)

            func.__name__ = original_func.__name__
            func.__doc__ = original_func.__doc__
            return func
        return decorator
    return guard

guard = _guard()
del _guard

