from .proxy import proxy, readOnlyError

def createSafeModule(real_module, attributes):
    attributes = set(attributes)

    name_repr = repr(real_module.__name__)
    try:
        module_file = real_module.__file__
    except AttributeError:
        name_repr += " (built-in)"
    else:
        name_repr += " from %r" % module_file
        attributes.add('__file__')

    attributes = frozenset(attributes)

    class SafeModule(object):
        __doc__ = real_module.__doc__
        __name__ = real_module.__name__
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
            return proxy(value)

        def __setattr__(self, name, value):
            readOnlyError()

        def __repr__(self):
            return "<SafeModule %s>" % (name_repr,)

    return SafeModule()

def _safe_import(__import__, module_whitelist):
    """
    Import a module.
    """
    def safe_import(name, globals={}, locals={}, fromlist=[], level=-1):
        try:
            attributes = module_whitelist[name]
        except KeyError:
            raise ImportError('Import "%s" blocked by the sandbox' % name)
        module = __import__(name, globals, locals, fromlist, level)
        return createSafeModule(module, attributes)
    return safe_import

