from __future__ import absolute_import
from .proxy import proxy, readOnlyError

def createSafeModule(real_module, attributes, safe_attributes):
    attributes = set(attributes)
    attributes |= set(safe_attributes)

    name_repr = repr(real_module.__name__)
    try:
        module_file = real_module.__file__
    except AttributeError:
        name_repr += " (built-in)"
    else:
        name_repr += " from %r" % module_file
        attributes.add('__file__')

    all_attributes = tuple(attributes)
    attributes = frozenset(attributes)
    safe_attributes = frozenset(safe_attributes)

    class SafeModule(object):
        __doc__ = real_module.__doc__
        __name__ = real_module.__name__
        __all__ = all_attributes
        __slots__ = tuple()

        def __delattr__(self, name):
            readOnlyError()

        def __dir__(self):
            return list(sorted(attributes))

        def __getattr__(self, name):
            if type(name) is not str:
                raise TypeError("expect string, not %s" % type(name).__name__)
            if name not in attributes:
                raise AttributeError("SafeModule %r has no attribute %r" % (self.__name__, name))
            value = getattr(real_module, name)
            if name not in safe_attributes:
                value = proxy(value)
            return value

        def __setattr__(self, name, value):
            readOnlyError()

        def __repr__(self):
            return "<SafeModule %s>" % (name_repr,)

    return SafeModule()

def _safe_import(__import__, module_whitelist):
    """
    Import a module.
    """
    def safe_import(name, globals=None, locals=None, fromlist=None, level=-1):
        try:
            attributes, safe_attributes = module_whitelist[name]
        except KeyError:
            raise ImportError('Import "%s" blocked by the sandbox' % name)
        if globals is None:
            globals = {}
        if locals is None:
            locals = {}
        if fromlist is None:
            fromlist = []
        module = __import__(name, globals, locals, fromlist, level)
        return createSafeModule(module, attributes, safe_attributes)
    return safe_import

