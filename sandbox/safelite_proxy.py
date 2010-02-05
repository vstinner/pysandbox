VERSION = 12

from inspect import getargs
from types import FunctionType
from os.path import realpath
from sandbox import SandboxError

# ------------------------------------------------------------------------------
# pseudo-klass-like namespase wrapper
# ------------------------------------------------------------------------------

def _Namespace(
    tuple=tuple, isinstance=isinstance, FunctionType=FunctionType,
    staticmethod=staticmethod,
    ):

    __private_data = {}

    def Namespace(*args, **kwargs):
        """Return a Namespace from the current scope or the given arguments."""

        class NamespaceObject(tuple):

            __slots__ = ()

            class __metaclass__(type):
                """A Namespace Context metaclass."""

                def __call__(klass, __getter):
                    for name, obj in __getter:
                        setattr(klass, name, obj)
                    return type.__call__(klass, __getter)

                def __str__(klass):
                    return 'NamespaceContext%s' % (tuple(klass.__dict__.keys()),)

            def __new__(klass, __getter):
                return tuple.__new__(klass, __getter)

        ns_items = []; populate = ns_items.append

        if args or kwargs:

            frame = None

            for arg in args:
                kwargs[arg.__name__] = arg

            for name, obj in kwargs.iteritems():
                if isinstance(obj, FunctionType):
                    populate((name, staticmethod(obj)))
                else:
                    populate((name, obj))

        del frame, args, kwargs

        # @/@ what should we do with __doc__ and __name__ ??

        return NamespaceObject(ns_items)

    return Namespace

Namespace = _Namespace()

del _Namespace

# ------------------------------------------------------------------------------
# guard dekorator
# ------------------------------------------------------------------------------

def guard(*varspec, **kwspec):
    def decorator(original_func):
#        if type(function) is not FunctionType:
#            raise TypeError("Argument to the guard decorator is not a function.")

        func_args = getargs(original_func.func_code)[0]
        len_args = len(func_args) - 1

        def func(*args, **kwargs):
            for i, param in enumerate(args):
                req = varspec[i]
                if type(param) is not req:
                    raise TypeError(
                        "%s has to be %r" % (func_args[i], req)
                        )
            for name, param in kwargs.iteritems():
                if name not in kwspec:
                    raise ValueError("no keyword argument %s" % name)
                req = kwspec[name]
                if type(param) is not req:
                    raise TypeError("%s has to be %r" % (name, req))
            return original_func(*args, **kwargs)

        func.__name__ = original_func.__name__
        func.__doc__ = original_func.__doc__
        return func
    return decorator

# ------------------------------------------------------------------------------
# file reader
# ------------------------------------------------------------------------------

def _FileReader(open_whitelist,
    open_file=open, type=type, TypeError=TypeError, Namespace=Namespace,
    any=any, realpath=realpath,
    ):

    @guard(str, str, int)
    def FileReader(filename, mode='r', buffering=0):
        """A secure file reader."""

        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")

        realname = realpath(filename)
        if not any(realname.startswith(path) for path in open_whitelist):
            raise SandboxError("Deny access to file %s" % filename)

        fileobj = open_file(filename, mode, buffering)

        def __repr__():
            return '<FileReader: %r>' % filename

        def close():
            fileobj.close()

        @guard(int)
        def read(bufsize=-1):
            return fileobj.read(bufsize)

        @guard(int)
        def readline(size=-1):
            return fileobj.readline(size)

        @guard(int)
        def readlines(size=-1):
            return fileobj.readlines(size)

        @guard(int, whence=int)
        def seek(offset, whence=0):
            fileobj.seek(offset, whence)

        def tell():
            return fileobj.tell()

        def is_closed():
            return fileobj.closed

        def is_atty():
            return fileobj.isatty()

        def get_encoding():
            return fileobj.encoding

        def get_mode():
            return fileobj.mode

        def get_name():
            return fileobj.name

        def get_newlines():
            return fileobj.newlines

        def __enter__():
            return fileobj.__enter__()

        def __exit__(value, errtype, traceback):
            return fileobj.__exit__(value, errtype, traceback)

        return Namespace(
            __repr__, __enter__, __exit__,
            close, read, readline, readlines, seek, tell, is_closed,
            is_atty, get_encoding, get_mode, get_name, get_newlines
            )

    return FileReader

