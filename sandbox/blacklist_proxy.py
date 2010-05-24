"""
Proxies using a blacklist policy.

Use a blacklist instead of a whitelist policy because __builtins__ HAVE TO
inherit from dict: Python/ceval.c uses PyDict_SetItem() and an inlined version
of PyDict_GetItem().
"""

from .proxy import proxy, readOnlyError

class ReadOnlyBuiltins(dict):
    """
    Type used for a read only version of the __builtins__ dictionary.

    Don't proxy __getattr__ because we suppose that __builtins__ only contains
    safe functions (not mutable objects).
    """
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

    def update(self, dict, **kw):
        readOnlyError()

def createDictProxy(data):
    # createReadOnlyDict() cannot be used for globals and locals because these
    # objects have to inherit from dict
    class DictProxy(ReadOnlyBuiltins):
        """
        Read only proxified dictionary used for exec locals and globals.
        """
        __slots__ = tuple()

        def __getitem__(self, key):
            value = data.__getitem__(key)
            return proxy(value)

        def get(self, key, default):
            try:
                value = data[key]
            except KeyError:
                return default
            else:
                return proxy(value)

        def keys(self):
            return data.keys()

        def iterkeys(self):
            return data.iterkeys()

        def values(self):
            return data.values()

        def itervalues(self):
            return data.itervalues()

        def items(self):
            return data.items()

        def iteritems(self):
            return data.iteritems()
    return DictProxy()

