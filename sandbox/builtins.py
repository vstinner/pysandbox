import __builtin__ as BUILTINS_MODULE
from types import FrameType
from sys import _getframe, version_info
import sys

from sandbox import SandboxError, USE_CSANDBOX
from .cpython import dictionary_of
from .safe_open import _safe_open
from .safe_import import _safe_import
from .restorable_dict import RestorableDict
from .proxy import createReadOnlyObject
from .blacklist_proxy import ReadOnlyBuiltins
if USE_CSANDBOX:
    from _sandbox import set_frame_builtins, set_interp_builtins

class CleanupBuiltins:
    """
    Deny unsafe builtins functions.
    """
    def __init__(self):
        self.get_frame_builtins = dictionary_of(FrameType)['f_builtins'].__get__
        self.builtin_dict = RestorableDict(BUILTINS_MODULE.__dict__)

    def enable(self, sandbox):
        config = sandbox.config

        # Remove all symbols not in the whitelist
        whitelist = config.builtins_whitelist
        keys = set(self.builtin_dict.dict.iterkeys())
        for key in keys - whitelist:
            del self.builtin_dict[key]

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
        open_whitelist = config.open_whitelist
        safe_open = _safe_open(open_whitelist)
        self.builtin_dict['open'] = safe_open
        if version_info < (3, 0):
            self.builtin_dict['file'] = safe_open

        # Replace __import__ function
        import_whitelist = config.import_whitelist
        self.builtin_dict['__import__'] = _safe_import(__import__, import_whitelist)

        # Replace exit function
        if 'exit' not in config.features:
            def safe_exit(code=0):
                raise SandboxError("exit() function blocked by the sandbox")
            self.builtin_dict['exit'] = safe_exit

        # Replace help function
        help_func = self.builtin_dict.dict.get('help')
        if help_func:
            if 'help' in config.features:
                self.builtin_dict['help'] = createReadOnlyObject(help_func)
            else:
                del self.builtin_dict['help']

        # Make builtins read only (enable restricted mode)
        safe_builtins = ReadOnlyBuiltins(self.builtin_dict.dict)
        if USE_CSANDBOX:
            set_frame_builtins(self.frame, safe_builtins)
            if not config.cpython_restricted:
                set_interp_builtins(safe_builtins)
        for module_dict in self.modules_dict:
            module_dict['__builtins__'] = safe_builtins
        self.main_module.__dict__['__builtins__'] = safe_builtins

    def disable(self, sandbox):
        # Restore builtin functions
        self.builtin_dict.restore()

        # Restore modifiable builtins
        if USE_CSANDBOX:
            set_frame_builtins(self.frame, self.builtins_dict)
            if not sandbox.config.cpython_restricted:
                set_interp_builtins(self.builtins_dict)
        for module_dict in self.modules_dict:
            module_dict['__builtins__'] = self.builtins_dict
        self.main_module.__dict__['__builtins__'] = BUILTINS_MODULE

