class SandboxError(Exception):
    pass

class Protection:
    def enable(self, sandbox):
        pass

    def disable(self, sandbox):
        pass

# CPython restricted mode is only available in Python 2.x
from sys import version_info, version
HAVE_CPYTHON_RESTRICTED = (version_info < (3, 0))
HAVE_PYPY = ('PyPy' in version)
del version, version_info

# Use the C module (_sandbox)
try:
    from _sandbox import set_error_class, version as _sandbox_version
except ImportError:
    if not HAVE_CPYTHON_RESTRICTED:
        raise SandboxError("_sandbox is required on Python 3.x")
    HAVE_CSANDBOX = False
else:
    HAVE_CSANDBOX = True
    set_error_class(SandboxError)
    del set_error_class
    if _sandbox_version != 2:
        raise SandboxError(
            "_sandbox version %s is not supported" % _sandbox_version)

from .config import SandboxConfig
from .sandbox_class import Sandbox

from .builtins import CleanupBuiltins
Sandbox.PROTECTIONS.append(CleanupBuiltins)

if not HAVE_PYPY:
    from .attributes import HideAttributes
    Sandbox.PROTECTIONS.append(HideAttributes)
else:
    # replace the follow line by "pass" to test PyPy
    raise SandboxError("PyPy is not supported yet")

from .stdio import ProtectStdio
Sandbox.PROTECTIONS.append(ProtectStdio)

if HAVE_CSANDBOX:
    from .code import DisableCode
    Sandbox.PROTECTIONS.append(DisableCode)

from .recursion import SetRecursionLimit
Sandbox.PROTECTIONS.append(SetRecursionLimit)

from .timeout import Timeout
