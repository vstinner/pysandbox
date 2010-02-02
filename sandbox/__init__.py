class SandboxError(Exception):
    pass

class Protection:
    def enable(self, sandbox):
        pass

    def disable(self, sandbox):
        pass

class Sandbox:
    protections = []

    def __init__(self, **kw):
        self.config = kw

    def __enter__(self):
        for protection in self.protections:
            protection.enable(self)

    def __exit__(self, type, value, traceback):
        for protection in self.protections:
            protection.disable(self)

from .builtins import CleanupBuiltins
Sandbox.protections.append(CleanupBuiltins())

from .attributes import HideAttributes
Sandbox.protections.append(HideAttributes())

