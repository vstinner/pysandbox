from os.path import realpath
from sandbox import SandboxError

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

def _safe_import(__import__, module_whitelist):
    """
    Import a module.
    """
    def safe_import(name, globals={}, locals={}, fromlist=[], level=-1):
        try:
            whitelist = module_whitelist[name]
        except KeyError:
            raise ImportError('Import "%s" blocked by the sandbox' % name)
        real_module = __import__(name, globals, locals, fromlist, level)
        module = SafeModule(real_module)
        for attr in whitelist:
            value = getattr(real_module, attr)
            # FIXME: copy/deepcopy the value?
            # Eg. sys.argv is a mutable list
            setattr(module, attr, value)
        return module
    return safe_import

