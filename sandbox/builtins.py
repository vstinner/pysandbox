import __builtin__
from types import FrameType
from sys import _getframe

from sandbox import BlockedFunction, SandboxError
from .cpython import dictionary_of
from .safe_open import _safe_open
from .safe_import import _safe_import
from .restorable_dict import RestorableDict

def readOnlyDict():
    raise SandboxError("Read only dictionary")

class ReadOnlyDict(dict):
    def __setitem__(self, key, value):
        readOnlyDict()

    def __delitem__(self, key):
        readOnlyDict()

class CleanupBuiltins:
    """
    Deny unsafe builtins functions.
    """
    def __init__(self):
        self.get_frame_locals = dictionary_of(FrameType)['f_locals'].__get__
        self.builtin_dict = RestorableDict(__builtin__.__dict__)

    def enable(self, sandbox):
        builtins_whitelist = sandbox.config.builtins_whitelist

        open_whitelist = sandbox.config.open_whitelist
        safe_open = _safe_open(open_whitelist)
        self.builtin_dict['open'] = safe_open
        self.builtin_dict['file'] = safe_open

        import_whitelist = sandbox.config.import_whitelist
        self.builtin_dict['__import__'] = _safe_import(__import__, import_whitelist)

        if 'exit' not in builtins_whitelist:
            def safe_exit(code=0):
                raise BlockedFunction("exit")
            self.builtin_dict['exit'] = safe_exit
            del self.builtin_dict['SystemExit']

        frame = _getframe(2)
        frame_locals = self.get_frame_locals(frame)
        safe_builtins = ReadOnlyDict(self.builtin_dict.dict)
        frame_locals['__builtins__'] = safe_builtins

    def disable(self, sandbox):
        self.builtin_dict.restore()

