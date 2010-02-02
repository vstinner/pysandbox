from types import FunctionType
try:
    from sys import _clear_type_cache
except ImportError:
    def _clear_type_cache():
        pass

from .cpython import dictionary_of
from .restorable_dict import RestorableDict

class HideAttributes:
    """
    Hide unsafe frame attributes from the Python space:
     * frame.xxx
     * function.xxx
    """
    def __init__(self):
        self.function_dict = RestorableDict(dictionary_of(FunctionType))

    def enable(self, sandbox):
        del self.function_dict['func_closure']

    def disable(self, sandbox):
        self.function_dict.restore()
        # Python 2.6+ uses a method cache: clear it to avoid errors
        _clear_type_cache()

