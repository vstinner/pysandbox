from types import FunctionType
from sandbox import SandboxError
from .guard import guard

builtin_function_or_method = type(len)

def _Namespace(tuple=tuple, isinstance=isinstance, FunctionType=FunctionType,
staticmethod=staticmethod, type=type):

    def Namespace(*args, **kwargs):
        class NamespaceObject(tuple):
            __slots__ = ()

            class __metaclass__(type):
                def __call__(klass, __getter):
                    for name, obj in __getter:
                        setattr(klass, name, obj)
                    return type.__call__(klass, __getter)

                def __str__(klass):
                    return 'NamespaceContext%s' % (tuple(klass.__dict__.keys()),)

            def __new__(klass, __getter):
                return tuple.__new__(klass, __getter)

        for arg in args:
            kwargs[arg.__name__] = arg

        ns_items = []
        for name, obj in kwargs.iteritems():
            if isinstance(obj, FunctionType):
                ns_items.append((name, staticmethod(obj)))
            else:
                ns_items.append((name, obj))

        # FIXME: what should we do with __doc__ and __name__ ??
        return NamespaceObject(ns_items)
    return Namespace

Namespace = _Namespace()
del _Namespace

def _FileProxy(
open_file=open, type=type, TypeError=TypeError, Namespace=Namespace,
any=any, guard=guard, ValueError=ValueError,
SandboxError=SandboxError):
    def FileProxy(fileobj, filename=None):
        def close():
            fileobj.close()

        @guard(bufsize=int)
        def read(bufsize=-1):
            return fileobj.read(bufsize)

        @guard(size=int)
        def readline(size=-1):
            return fileobj.readline(size)

        @guard(size=int)
        def readlines(size=-1):
            return fileobj.readlines(size)

        @guard(offset=int, whence=int)
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

        # FIXME: @guard(value=?, errtype=?, traceback=?)
        def __exit__(value, errtype, traceback):
            return fileobj.__exit__(value, errtype, traceback)

        args = [__enter__, __exit__,
            close, read, readline, readlines, seek, tell, is_closed,
            is_atty, get_encoding, get_mode, get_name, get_newlines]

        if filename:
            def __repr__():
                return '<FileReader: %r>' % filename
            args.append(__repr__)

        return Namespace(*args)
    return FileProxy

FileProxy = _FileProxy()
del _FileProxy

SAFE_TYPES = (
    type(None), bool,
    int, long, 
    str, unicode, 
    builtin_function_or_method, FunctionType, 
)

def _proxy(safe_types=SAFE_TYPES, file=file):
    def proxy(value):
        if isinstance(value, safe_types):
            # Safe type, no need to create a proxy
            return value
        elif isinstance(value, tuple):
            return tuple(
                proxy(item)
                for item in value)
        elif isinstance(value, list):
            return list(
                proxy(item)
                for item in value)
        elif isinstance(value, dict):
            return dict(
                (proxy(key), proxy(value))
                for key, value in value.iteritems())
        elif isinstance(value, file):
            return FileProxy(value)
        else:
            raise TypeError("Unable to proxy a value of type %s" % type(value))
    return proxy

proxy = _proxy()
del _proxy

