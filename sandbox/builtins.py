import __builtin__
from types import FrameType
from sys import _getframe
import sys

from sandbox import (BlockedFunction, SandboxError,
    SET_FRAME_BUILTINS, USE_CPYTHON_RESTRICTED)
from .cpython import dictionary_of
from .safe_open import _safe_open
from .safe_import import _safe_import
from .restorable_dict import RestorableDict

if SET_FRAME_BUILTINS:
    from .cpython_hack import set_frame_builtins
if not USE_CPYTHON_RESTRICTED:
    from .cpython_hack import set_interp_builtins

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
        self.get_frame_builtins = dictionary_of(FrameType)['f_builtins'].__get__
        self.builtin_dict = RestorableDict(__builtin__.__dict__)

    def enable(self, sandbox):
        # Get frame builtins
        self.frame = _getframe(2)
        self.builtins_dict = self.get_frame_builtins(self.frame)

        # Get module list
        self.modules_dict = []
        for name, module in sys.modules.iteritems():
            if module is None:
                continue
            if '__builtins__' not in module.__dict__:
                # builtin modules have no __dict__ attribute
                continue
            if name == "__main__":
                 # __main__ is a special case
                continue
            self.modules_dict.append(module.__dict__)
        self.main_module = sys.modules['__main__']

        # Replace open and file functions
        open_whitelist = sandbox.config.open_whitelist
        safe_open = _safe_open(open_whitelist)
        self.builtin_dict['open'] = safe_open
        self.builtin_dict['file'] = safe_open

        # Replace __import__ function
        import_whitelist = sandbox.config.import_whitelist
        self.builtin_dict['__import__'] = _safe_import(__import__, import_whitelist)

        # Replace exit function
        if 'exit' not in sandbox.config.builtins_whitelist:
            def safe_exit(code=0):
                raise BlockedFunction("exit")
            self.builtin_dict['exit'] = safe_exit
            del self.builtin_dict['SystemExit']

        # Make builtins read only (enable restricted mode)
        safe_builtins = ReadOnlyDict(self.builtin_dict.dict)
        if SET_FRAME_BUILTINS:
            set_frame_builtins(self.frame, safe_builtins)
        if not USE_CPYTHON_RESTRICTED:
            set_interp_builtins(self.frame, safe_builtins)
        for module_dict in self.modules_dict:
            module_dict['__builtins__'] = safe_builtins
        self.main_module.__dict__['__builtins__'] = safe_builtins

    def disable(self, sandbox):
        # Restore builtin functions
        self.builtin_dict.restore()

        # Restore modifiable builtins
        if SET_FRAME_BUILTINS:
            set_frame_builtins(self.frame, self.builtins_dict)
        if not USE_CPYTHON_RESTRICTED:
            set_interp_builtins(self.frame, self.builtins_dict)
        for module_dict in self.modules_dict:
            module_dict['__builtins__'] = self.builtins_dict
        self.main_module.__dict__['__builtins__'] = __builtin__

