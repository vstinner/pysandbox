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
    raise SandboxError("Sandbox deny modify operation on a read only object")

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

def createObjectProxy(obj, SandboxError=SandboxError,
isinstance=isinstance, MethodType=MethodType):
    obj_class = obj.__class__

    class ObjectProxy:
        __name__ = proxy(obj_class.__name__)
        __doc__ = proxy(obj_class.__doc__)
        __module__ = proxy(obj_class.__module__)

        def __getattr__(self, name):
            value = getattr(obj, name)
            if isinstance(value, MethodType):
                value = MethodType(value.im_func, self, self.__class__)
            else:
                value = proxy(value)
            return value

        def __setattr__(self, name, value):
            readOnlyError()

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

