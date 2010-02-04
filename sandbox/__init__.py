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

DEFAULT_CONFIG = {
    # open() whitelist: see safe_open()
    'open_whitelist': tuple(),

    # import whitelist: see safe_import()
    'import_whitelist': {
        'sys': ('api_version', 'byteorder', 'copyright', 'hexversion', 'maxint', 'maxunicode', 'subversion', 'version'),
    },
}

class Sandbox:
    protections = []

    def __init__(self, **kw):
        self.config = dict(DEFAULT_CONFIG)
        self.config.update(kw)

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

