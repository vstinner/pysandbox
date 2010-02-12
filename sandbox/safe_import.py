from .proxy import proxy

class SafeModule(object):
    def __init__(self, module):
        self.__name = repr(module.__name__)
        try:
            self.__file = module.__file__
            self.__name += " from %r" % self.__file__
        except AttributeError:
            self.__name += " (built-in)"
        self.__name__ = module.__name__
        self.__doc__ = module.__doc__

    def __repr__(self):
        return "<SafeModule %s>" % (self.__name,)

def createSafeModule(module, attributes):
    safe = SafeModule(module)
    for attr in attributes:
        value = getattr(module, attr)
        value = proxy(value)
        setattr(safe, attr, value)
    return safe

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

