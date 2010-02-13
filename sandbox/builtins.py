import __builtin__
from sys import _getframe

from sandbox import BlockedFunction, SandboxError
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
        self.builtin_dict = RestorableDict(__builtin__.__dict__)

    def enable(self, sandbox):
        self.frame = _getframe(2)
        self.frame_locals = self.frame.f_locals
        self.local_builtins = self.frame_locals.get('__builtins__', None)

        open_whitelist = sandbox.config.open_whitelist
        safe_open = _safe_open(open_whitelist)
        self.builtin_dict['open'] = safe_open
        self.builtin_dict['file'] = safe_open

        import_whitelist = sandbox.config.import_whitelist
        self.builtin_dict['__import__'] = _safe_import(__import__, import_whitelist)

        if 'exit' not in sandbox.config.builtins_whitelist:
            def safe_exit(code=0):
                raise BlockedFunction("exit")
            self.builtin_dict['exit'] = safe_exit
            del self.builtin_dict['SystemExit']

        safe_builtins = ReadOnlyDict(self.builtin_dict.dict)

        if self.local_builtins is not None:
            self.frame_locals['__builtins__'] = safe_builtins

    def disable(self, sandbox):
        self.builtin_dict.restore()
        if self.local_builtins is not None:
            self.frame_locals['__builtins__'] = self.local_builtins

