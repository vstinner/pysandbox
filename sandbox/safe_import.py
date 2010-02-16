from .proxy import proxy, readOnlyError

class SafeModule(object):
    def __init__(self, module, attributes):
        _set = object.__setattr__
        name_repr = repr(module.__name__)
        try:
            _set(self, '__file',  module.__file__)
            name_repr += " from %r" % self.__file__
        except AttributeError:
            name_repr += " (built-in)"
        _set(self, '__name_repr',  name_repr)
        _set(self, '__name__', module.__name__)
        _set(self, '__doc__', module.__doc__)
        for key, value in attributes.iteritems():
            _set(self, key, value)

    def __setattr__(self, name, value):
        readOnlyError()

    def __repr__(self):
        return "<SafeModule %s>" % (self.__name_repr,)

def createSafeModule(module, attributes):
    safe_attributes = {}
    for attr in attributes:
        value = getattr(module, attr)
        value = proxy(value)
        safe_attributes[attr] = value
    return SafeModule(module, safe_attributes)

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

