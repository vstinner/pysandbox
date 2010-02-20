"""
Proxies using a whitelist policy.
"""

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

class Proxy(object):
    __slots__ = tuple()

def copyProxyMethods(real_object, proxy_class):
    # Copy methods from the real object because object has default
    # implementations
    for name in ('__repr__', '__str__', '__hash__', '__call__'):
        if not hasattr(real_object, name):
            continue
        func = getattr(real_object, name)
        func = createMethodProxy(func)
        setattr(proxy_class, name, func)

class ReadOnlySequence(Proxy):
    # Child classes have to implement: __iter__, __getitem__, __len__

    __slots__ = tuple()

    def __setitem__(self, key, value):
        readOnlyError()

    def __setslice__(self, start, end, value):
        readOnlyError()

    def __delitem__(self, key):
        readOnlyError()

    def __delslice__(self, start, end):
        readOnlyError()

def createReadOnlyDict(data):
    class ReadOnlyDict(ReadOnlySequence):
        def __getitem__(self, index):
            value = data.__getitem__(index)
            return proxy(value)

    copyProxyMethods(data, ReadOnlyDict)
    return ReadOnlyDict()

def createReadOnlyList(data):
    class ReadOnlyList(ReadOnlySequence):
        __slots__ = tuple()
        __doc__ = data.__doc__

        # FIXME: __contains__, count, index, __reversed__
        # FIXME: __add__, __iadd__, __imul__, __mul__, __rmul__
        # FIXME: compare: __eq__, __ge__, __gt__, __le__, __lt__, __ne__
        # FIXME: other: __reduce__, __reduce_ex__

        def append(self, value):
            readOnlyError()

        def extend(self, iterable):
            readOnlyError()

        def __getitem__(self, index):
            value = data.__getitem__(index)
            return proxy(value)

        def __getslice__(self, start, end):
            value = data.__getslice__(start, end)
            return proxy(value)

        def insert(self, index, object):
            readOnlyError()

        def pop(self, index=None):
            readOnlyError()

        def remove(self, value):
            readOnlyError()

        def reverse(self, value):
            readOnlyError()

        def sort(self, cmp=None, key=None, reverse=False):
            readOnlyError()

    copyProxyMethods(data, ReadOnlyList)
    return ReadOnlyList()

class ReadOnlyObject(Proxy):
    __slots__ = tuple()

    def __setattr__(self, name, value):
        readOnlyError()

    def __delattr__(self, name):
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
    class ObjectProxy(ReadOnlyObject):
        __slots__ = tuple()
        __doc__ = real_object.__doc__

        def __getattr__(self, name):
            value = getattr(real_object, name)
            if isinstance(value, MethodType):
                value = MethodType(value.im_func, self, self.__class__)
            else:
                value = proxy(value)
            return value

    copyProxyMethods(real_object, ObjectProxy)
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
            return createReadOnlyList(value)
        elif isinstance(value, dict):
            return createReadOnlyDict(value)
        elif isinstance(value, (file, ClassType, InstanceType)):
            return createObjectProxy(value)
        else:
            raise TypeError("Unable to proxy a value of type %s" % type(value))
    return proxy

proxy = _proxy()
del _proxy

