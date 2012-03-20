from __future__ import absolute_import
from types import FunctionType, FrameType, GeneratorType
from sys import version_info
try:
    from sys import _clear_type_cache
except ImportError:
    # Python < 2.6 has no type cache, so we don't have to clear it
    def _clear_type_cache():
        pass

from .cpython import dictionary_of
from .restorable_dict import RestorableDict

builtin_function = type(len)

class HideAttributes:
    """
    Hide unsafe frame attributes from the Python space
    """
    def __init__(self):
        self.dict_dict = RestorableDict(dictionary_of(dict))
        self.function_dict = RestorableDict(dictionary_of(FunctionType))
        self.frame_dict = RestorableDict(dictionary_of(FrameType))
        self.type_dict = RestorableDict(dictionary_of(type))
        self.builtin_func_dict = RestorableDict(dictionary_of(builtin_function))
        self.generator_dict = RestorableDict(dictionary_of(GeneratorType))

    def enable(self, sandbox):
        if not sandbox.config.cpython_restricted:
            # Deny access to func.func_code to avoid an attacker to modify a
            # trusted function: replace the code of the function
            hide_func_code = True
        else:
            # CPython restricted mode already denies read and write access to
            # function attributes
            hide_func_code = False

        # Blacklist all dict methods able to modify a dict, to protect
        # ReadOnlyBuiltins
        for name in (
        '__init__', 'clear', '__delitem__', 'pop', 'popitem',
        'setdefault', '__setitem__', 'update'):
            del self.dict_dict[name]
        if version_info < (3, 0):
            # pysandbox stores trusted objects in closures: deny access to
            # closures to not leak these secrets
            del self.function_dict['func_closure']
            del self.function_dict['func_globals']
            if hide_func_code:
                del self.function_dict['func_code']
            del self.function_dict['func_defaults']
        if version_info >= (2, 6):
            del self.function_dict['__closure__']
            del self.function_dict['__globals__']
            if hide_func_code:
                del self.function_dict['__code__']
            del self.function_dict['__defaults__']
        del self.frame_dict['f_locals']

        # Hiding type.__bases__ crashs CPython 2.5 because of a infinite loop
        # in PyErr_ExceptionMatches(): it calls abstract_get_bases() but
        # abstract_get_bases() fails and call PyErr_ExceptionMatches() ...
        if version_info >= (2, 6):
            # Setting __bases__ crash Python < 3.3a2
            # http://bugs.python.org/issue14199
            del self.type_dict['__bases__']

        # object.__subclasses__ leaks the file type in Python 2
        # and (indirectly) the FileIO file in Python 3
        del self.type_dict['__subclasses__']
        del self.builtin_func_dict['__self__']
        _clear_type_cache()

    def disable(self, sandbox):
        self.dict_dict.restore()
        self.function_dict.restore()
        self.frame_dict.restore()
        self.type_dict.restore()
        self.builtin_func_dict.restore()
        self.generator_dict.restore()
        # Python 2.6+ uses a method cache: clear it to avoid errors
        _clear_type_cache()

