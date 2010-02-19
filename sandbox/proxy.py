from types import FunctionType, ClassType, InstanceType, MethodType
from sandbox import SandboxError

builtin_function_or_method = type(len)

SAFE_TYPES = (
    type(None), bool,
    int, long,
    str, unicode,
    builtin_function_or_method, FunctionType,
)

def readOnlyError():
    raise SandboxError("Read only object")

class ReadOnlyDict(dict):
    def __setitem__(self, key, value):
        readOnlyError()

    def __delitem__(self, key):
        readOnlyError()

class ReadOnlyList(list):
    def append(self, value):
        readOnlyError()

    def remove(self, value):
        readOnlyError()

    def __setitem__(self, key, value):
        readOnlyError()

    def __setslice__(self, start, end, value):
        readOnlyError()

    def __delitem__(self, key):
        readOnlyError()

def createMethodProxy(method_wrapper):
    # Use object with __slots__ to deny the modification of attributes
    # and the creation of new attributes
    class MethodProxy(object):
        __slots__ = ("__name__", "__doc__")
        __doc__ = method_wrapper.__doc__
        def __call__(self, *args, **kw):
            value = method_wrapper(*args, **kw)
            value = proxy(value)
            return value
    func = MethodProxy()
    func.__name__ = method_wrapper.__name__
    return func

def createObjectProxy(real_object, readOnlyError=readOnlyError,
isinstance=isinstance, MethodType=MethodType):
    # Use object with __slots__ to deny the modification of attributes
    # and the creation of new attributes
    class ObjectProxy(object):
        __doc__ = real_object.__doc__
        __slots__ = tuple()

        def __getattr__(self, name):
            value = getattr(real_object, name)
            if isinstance(value, MethodType):
                value = MethodType(value.im_func, self, self.__class__)
            else:
                value = proxy(value)
            return value

        def __setattr__(self, name, value):
            readOnlyError()

        def __delattr__(self, name):
            readOnlyError()

    # Copy some methods because object has default implementations
    for name in ('__repr__', '__str__', '__hash__', '__call__'):
        if not hasattr(real_object, name):
            continue
        func = getattr(real_object, name)
        func = createMethodProxy(func)
        setattr(ObjectProxy, name, func)

    return ObjectProxy()

def _proxy(safe_types=SAFE_TYPES, file=file,
ClassType=ClassType, InstanceType=InstanceType, TypeError=TypeError):
    def proxy(value):
        if isinstance(value, safe_types):
            # Safe type, no need to create a proxy
            return value
        elif isinstance(value, tuple):
            return tuple(
                proxy(item)
                for item in value)
        elif isinstance(value, list):
            return ReadOnlyList(
                proxy(item)
                for item in value)
        elif isinstance(value, dict):
            return ReadOnlyDict(
                (proxy(key), proxy(value))
                for key, value in value.iteritems())
        elif isinstance(value, (file, ClassType, InstanceType)):
            return createObjectProxy(value)
        else:
            raise TypeError("Unable to proxy a value of type %s" % type(value))
    return proxy

proxy = _proxy()
del _proxy

