from types import FunctionType

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

