from sandbox import Sandbox, SandboxError
from sandbox.test import createSandbox, createSandboxConfig

def test_import():
    def import_blocked():
        try:
            import os
        except ImportError, err:
            assert str(err) == 'Import "os" blocked by the sandbox'
        else:
            assert False
    createSandbox().call(import_blocked)

    # import is allowed outside the sandbox
    import os

def test_import_whitelist():
    # sys.version is allowed by the sandbox
    import sys
    sys_version = sys.version
    del sys

    config = createSandboxConfig()
    config.allowModule('sys', 'version')
    def import_sys():
        import sys
        assert sys.__name__ == 'sys'
        assert sys.version == sys_version
    Sandbox(config).call(import_sys)

def test_readonly_import():
    config = createSandboxConfig()
    config.allowModule('sys', 'version')
    def readonly_module():
        import sys

        try:
            sys.version = '3000'
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False

        try:
            object.__setattr__(sys, 'version', '3000')
        except AttributeError, err:
            assert str(err) == "'SafeModule' object has no attribute 'version'"
        else:
            assert False
    Sandbox(config).call(readonly_module)

