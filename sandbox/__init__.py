class Protection:
    def enable(self):
        pass

    def disable(self):
        pass


class Sandbox:
    protections = []

    def __enter__(self):
        for protection in self.protections:
            protection.enable()

    def __exit__(self, type, value, traceback):
        for protection in self.protections:
            protection.disable()

from .builtins import CleanupBuiltins
Sandbox.protections.append(CleanupBuiltins())

from .attributes import HideAttributes
Sandbox.protections.append(HideAttributes())

