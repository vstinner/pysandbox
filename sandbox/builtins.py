import __builtin__
from types import FrameType
from sys import _getframe

from .cpython import dictionary_of
from .safe_open import _safe_open
from .restorable_dict import RestorableDict

class CleanupBuiltins:
    """
    Deny unsafe builtins functions.
    """
    def __init__(self):
        self.get_frame_locals = dictionary_of(FrameType)['f_locals'].__get__
        self.builtin_dict = RestorableDict(__builtin__.__dict__)

    def enable(self, sandbox):
        whitelist = sandbox.config.get('open_whitelist', None)
        safe_open = _safe_open(open, whitelist)
        self.builtin_dict['open'] = safe_open
        self.builtin_dict['file'] = safe_open

        frame = _getframe(2)
        frame_locals = self.get_frame_locals(frame)
        frame_locals['__builtins__'] = self.builtin_dict.copy()

    def disable(self, sandbox):
        self.builtin_dict.restore()

