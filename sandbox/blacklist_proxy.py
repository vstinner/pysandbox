"""
Proxies using a blacklist policy.

Use a blacklist instead of a whitelist policy because __builtins__ HAVE TO
inherit from dict: Python/ceval.c uses PyDict_SetItem() and an inlined version
of PyDict_GetItem().
"""

from .proxy import readOnlyError

# If you update this class, update also HideAttributes.enable()
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

