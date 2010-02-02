from .cpython import dictionary_of
from types import FunctionType

class Dict:
    def __init__(self, dict):
        self.dict = dict
        self.removed = {}

    def __delitem__(self, key):
        self.removed[key] = self.dict.pop(key)

    def restore(self):
        self.dict.update(self.removed)

class HideAttributes:
    """
    Hide unsafe frame attributes from the Python space:
     * frame.xxx
     * function.xxx
    """
    def __init__(self):
        self.function_dict = Dict(dictionary_of(FunctionType))

    def enable(self):
        del self.function_dict['func_closure']

    def disable(self):
        self.function_dict.restore()

