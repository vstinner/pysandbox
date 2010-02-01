import __builtin__
from types import FrameType
from sys import _getframe

from .cpython import dictionary_of

class CleanupBuiltins:
    def __init__(self):
        self.unsafe_builtins = ['open']
        self.get_frame_locals = dictionary_of(FrameType)['f_locals'].__get__
        self.original = {}

    def enable(self):
        self.original.clear()
        self.builtin_dict = __builtin__.__dict__
        for item in self.unsafe_builtins:
            self.original[item] = self.builtin_dict.pop(item)

        frame = _getframe(2)
        frame_locals = self.get_frame_locals(frame)
        frame_locals['__builtins__'] = self.builtin_dict.copy()

    def disable(self):
        for key, value in self.original.iteritems():
            self.builtin_dict[key] = value

