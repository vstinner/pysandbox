class SandboxError(Exception):
    pass

class BlockedFunction(SandboxError):
    def __init__(self, name):
        SandboxError.__init__(self, "Function %s() blocked by the sandbox" % name)

class Protection:
    def enable(self, sandbox):
        pass

    def disable(self, sandbox):
        pass

USE_CPYTHON_RESTRICTED = True
SET_FRAME_BUILTINS = True

from .config import SandboxConfig
from .sandbox_class import Sandbox

from .builtins import CleanupBuiltins
Sandbox.PROTECTIONS.append(CleanupBuiltins)

from .attributes import HideAttributes
Sandbox.PROTECTIONS.append(HideAttributes)

from .stdio import ProtectStdio
Sandbox.PROTECTIONS.append(ProtectStdio)

