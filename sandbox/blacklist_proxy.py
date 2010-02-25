"""
Proxies using a blacklist policy.
"""

from .proxy import readOnlyError

# Use a blacklist instead of a whitelist policy because __builtins__ HAVE TO
# inherit from dict: Python/ceval.c uses PyDict_SetItem() and an inlined
# version of PyDict_GetItem().
#
# Don't proxy __getattr__ because I suppose that __builtins__ only contains
# safe functions (not mutable objects).
class ReadOnlyBuiltins(dict):
    __slots__ = tuple()

    def clear(self):
        readOnlyError()

    def __delitem__(self, key):
        readOnlyError()

    def pop(self, key, default=None):
        readOnlyError()

    def popitem(self):
        readOnlyError()

    def setdefault(self, key, value):
        readOnlyError()

    def __setitem__(self, key, value):
        readOnlyError()

    def __setslice__(self, start, end, value):
        readOnlyError()

    def update(self, dict, **kw):
        readOnlyError()

def createDictProxy(data):
    class DictProxy(ReadOnlyBuiltins):
        __slots__ = tuple()

        def __getitem__(self, index):
            value = data.__getitem__(index)
            return proxy(value)
    return DictProxy()

