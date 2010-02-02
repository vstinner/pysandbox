import __builtin__
from types import FrameType
from sys import _getframe

from .cpython import dictionary_of
from .safe_open import safe_open
from .restorable_dict import RestorableDict

class CleanupBuiltins:
    """
    Deny unsafe builtins functions.
    """
    def __init__(self):
        #self.unsafe_builtins = ['open', 'file', 'execfile', 'reload', 'compile', 'input', 'eval']
        self.unsafe_builtins = (
            # open a file
            'open', 'file',
        )
        self.get_frame_locals = dictionary_of(FrameType)['f_locals'].__get__
        self.builtin_dict = RestorableDict(__builtin__.__dict__)
        self.original = {}

    def enable(self):
        self.builtin_dict['open'] = safe_open
        self.builtin_dict['file'] = safe_open

        frame = _getframe(2)
        frame_locals = self.get_frame_locals(frame)
        frame_locals['__builtins__'] = self.builtin_dict.copy()

    def disable(self):
        self.builtin_dict.restore()

