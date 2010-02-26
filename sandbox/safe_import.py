from .proxy import proxy, readOnlyError

def createSafeModule(real_module, attributes):
    attributes = tuple(attributes) + ('__file__',)

    name_repr = repr(real_module.__name__)
    if hasattr(real_module, '__file__'):
        attributes += ('__file__',)
        name_repr += " from %r" % real_module.__file__
    else:
        name_repr += " (built-in)"

    class SafeModule(object):
        __doc__ = real_module.__doc__
        __name__ = real_module.__name__
        __slots__ = tuple()

        def __delattr__(self, name):
            readOnlyError()

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
            whitelist = module_whitelist[name]
        except KeyError:
            raise ImportError('Import "%s" blocked by the sandbox' % name)
        module = __import__(name, globals, locals, fromlist, level)
        return createSafeModule(module, whitelist)
    return safe_import

