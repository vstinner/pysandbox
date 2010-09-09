"""
Proxies using a whitelist policy.
"""

from sys import version_info
if version_info < (3, 0):
    from types import NoneType, ClassType, InstanceType
    OBJECT_TYPES = (file, ClassType, InstanceType)
    BYTES_TYPE = str
    UNICODE_TYPE = unicode
    def is_callable(obj):
        return callable(obj)
else:
    # Python 3 has no NoneType
    NoneType = type(None)
    OBJECT_TYPES = tuple()
    # 2to3 script converts str to str instead of bytes
    BYTES_TYPE = bytes
    UNICODE_TYPE = str
    def is_callable(obj):
        return any("__call__" in cls.__dict__ for cls in type(obj).__mro__)

from types import MethodType, FrameType
from sandbox import SandboxError

builtin_function_or_method = type(len)

SAFE_TYPES = (
    NoneType,
    bool, int, long, float,
    BYTES_TYPE, UNICODE_TYPE,
    FrameType,
)

def readOnlyError():
    raise SandboxError("Read only object")

def createMethodProxy(method_wrapper):
    # Use object with __slots__ to deny the modification of attributes
    # and the creation of new attributes
    class MethodProxy(object):
        __slots__ = ("__name__", "__doc__")
        __doc__ = method_wrapper.__doc__
        def __call__(self, *args, **kw):
            value = method_wrapper(*args, **kw)
            return proxy(value)
    func = MethodProxy()
    func.__name__ = method_wrapper.__name__
    return func

def copyProxyMethods(real_object, proxy_class):
    for name in (
    # Copy methods from the real object because the object type has default
    # implementations
    '__repr__', '__str__', '__hash__', '__call__',
    # Copy __enter__ and __exit__ because the WITH_STATEMENT bytecode uses
    # special_lookup() which reads type(obj).attr instead of obj.attr
    '__enter__', '__exit__',
    ):
        if not hasattr(real_object, name):
            continue
        func = getattr(real_object, name)
        if func is not None:
            func = createMethodProxy(func)
        setattr(proxy_class, name, func)

class ReadOnlySequence(object):
    __slots__ = tuple()

    # Child classes have to implement: __iter__, __getitem__, __len__

    def __delitem__(self, key):
        readOnlyError()

    def __setitem__(self, key, value):
        readOnlyError()

def createReadOnlyDict(real_dict):
    class ReadOnlyDict(ReadOnlySequence):
        __slots__ = tuple()
        __doc__ = real_dict.__doc__

        # FIXME: fromkeys
        # FIXME: compare: __cmp__, __eq__', __ge__, __gt__, __le__, __lt__, __ne__,
        # FIXME: other __reduce__, __reduce_ex__

        def clear(self):
            readOnlyError()

        def __contains__(self, key):
            return (key in real_dict)

        def copy(self):
            return dict(item for item in self.iteritems())

        def get(self, key, default=None):
            if key not in real_dict:
                return default
            value = real_dict[key]
            return proxy(value)

        def __getitem__(self, index):
            value = real_dict.__getitem__(index)
            return proxy(value)

        if version_info < (3, 0):
            def has_key(self, key):
                return (key in real_dict)

        def items(self):
            return list(self.iteritems())

        def __iter__(self):
            return self.iterkeys()

        def iteritems(self):
            for item in real_dict.iteritems():
                key, value = item
                yield (proxy(key), proxy(value))

        def iterkeys(self):
            for key in real_dict.iterkeys():
                yield proxy(key)

        def itervalues(self):
            for value in real_dict.itervalues():
                yield proxy(value)

        def keys(self):
            return list(self.iterkeys())

        def __len__(self):
            return len(real_dict)

        def pop(self, key, default=None):
            readOnlyError()

        def popitem(self):
            readOnlyError()

        def setdefault(self, key, default=None):
            readOnlyError()

        def update(self, other, **items):
            readOnlyError()

        def values(self):
            return list(self.itervalues())

    copyProxyMethods(real_dict, ReadOnlyDict)
    return ReadOnlyDict()

def createReadOnlyList(real_list):
    class ReadOnlyList(ReadOnlySequence):
        __slots__ = tuple()
        __doc__ = real_list.__doc__

        # FIXME: operators: __add__, __iadd__, __imul__, __mul__, __rmul__
        # FIXME: compare: __eq__, __ge__, __gt__, __le__, __lt__, __ne__
        # FIXME: other: __reduce__, __reduce_ex__

        def append(self, value):
            readOnlyError()

        def __contains__(self, value):
            return (value in real_list)

        def count(self, value):
            return real_list.count(value)

        def __delslice__(self, start, end):
            readOnlyError()

        def extend(self, iterable):
            readOnlyError()

        def __getitem__(self, index):
            value = real_list.__getitem__(index)
            return proxy(value)

        def __getslice__(self, start, end):
            value = real_list.__getslice__(start, end)
            return proxy(value)

        def index(self, value):
            return real_list.index(value)

        def insert(self, index, object):
            readOnlyError()

        def __iter__(self):
            for value in real_list:
                yield proxy(value)

        def __len__(self):
            return len(real_list)

        def pop(self, index=None):
            readOnlyError()

        def remove(self, value):
            readOnlyError()

        def reverse(self, value):
            readOnlyError()

        def __reversed__(self):
            for value in real_list.__reversed__():
                yield proxy(value)

        def __setslice__(self, start, end, value):
            readOnlyError()

        def sort(self, cmp=None, key=None, reverse=False):
            readOnlyError()

    copyProxyMethods(real_list, ReadOnlyList)
    return ReadOnlyList()

def createReadOnlyObject(real_object, readOnlyError=readOnlyError,
isinstance=isinstance, MethodType=MethodType):
    # Use object with __slots__ to deny the modification of attributes
    # and the creation of new attributes
    class ReadOnlyObject(object):
        __slots__ = tuple()
        __doc__ = real_object.__doc__

        def __delattr__(self, name):
            readOnlyError()

        def __getattr__(self, name):
            value = getattr(real_object, name)
            if isinstance(value, MethodType):
                value = MethodType(value.im_func, self, self.__class__)
            return proxy(value)

        def __setattr__(self, name, value):
            readOnlyError()

    copyProxyMethods(real_object, ReadOnlyObject)
    return ReadOnlyObject()

def copy_callable_attributes(original, copy):
    for name in ('__name__', '__doc__'):
        try:
            value = getattr(original, name)
        except AttributeError:
            continue
        try:
            setattr(copy, name, value)
        except RuntimeError:
            # function attributes not accessible in restricted mode
            pass

def callback_proxy(proxy, callback):
    def _callback_proxy(*args, **kw):
        result = callback(*args, **kw)
        return proxy(result)
    copy_callable_attributes(callback, _callback_proxy)
    return _callback_proxy

def _proxy():
    def proxy(value):
        if isinstance(value, SAFE_TYPES):
            # Safe type, no need to create a proxy
            return value
        elif is_callable(value):
            return callback_proxy(proxy, value)
        elif isinstance(value, tuple):
            return tuple(
                proxy(item)
                for item in value)
        elif isinstance(value, list):
            return createReadOnlyList(value)
        elif isinstance(value, dict):
            return createReadOnlyDict(value)
        elif isinstance(value, OBJECT_TYPES):
            return createReadOnlyObject(value)
        else:
            raise TypeError("Unable to proxy a value of type %s" % type(value))
    return proxy
proxy = _proxy()
del _proxy

