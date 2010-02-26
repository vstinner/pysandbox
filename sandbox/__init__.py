class SandboxError(Exception):
    pass

class Protection:
    def enable(self, sandbox):
        pass

    def disable(self, sandbox):
        pass

USE_CPYTHON_HACKS = True

from .config import SandboxConfig
from .sandbox_class import Sandbox

from .builtins import CleanupBuiltins
Sandbox.PROTECTIONS.append(CleanupBuiltins)

from .attributes import HideAttributes
Sandbox.PROTECTIONS.append(HideAttributes)

from .stdio import ProtectStdio
Sandbox.PROTECTIONS.append(ProtectStdio)

