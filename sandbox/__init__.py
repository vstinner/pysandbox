class SandboxError(Exception):
    pass

class Protection:
    def enable(self, sandbox):
        pass

    def disable(self, sandbox):
        pass

# Use the C module (_sandbox)
USE_CSANDBOX = True

if USE_CSANDBOX:
    from _sandbox import set_error_class, version as _sandbox_version
    set_error_class(SandboxError)
    del set_error_class
    if _sandbox_version != 1:
        raise SandboxError("Unknown _sandbox version (%s)" % _sandbox_version)

from .config import SandboxConfig
from .sandbox_class import Sandbox

from .builtins import CleanupBuiltins
Sandbox.PROTECTIONS.append(CleanupBuiltins)

from .attributes import HideAttributes
Sandbox.PROTECTIONS.append(HideAttributes)

from .stdio import ProtectStdio
Sandbox.PROTECTIONS.append(ProtectStdio)

if USE_CSANDBOX:
    from .code import DisableCode
    Sandbox.PROTECTIONS.append(DisableCode)

from .timeout import Timeout
