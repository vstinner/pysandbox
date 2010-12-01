from sandbox import Sandbox, HAVE_CPYTHON_RESTRICTED, HAVE_CSANDBOX, HAVE_PYPY
from sandbox.test import SkipTest, createSandboxConfig
from ._test_restricted import _test_restricted

if not HAVE_CPYTHON_RESTRICTED:
    raise SkipTest("restricted mode is specific to Python 2.x")

def test_frame_restricted():
    from sys import _getframe

    config = createSandboxConfig(cpython_restricted=True)
    def check_frame_restricted():
        frame = _getframe()
        assert frame.f_restricted == True
    Sandbox(config).call(check_frame_restricted)

    if HAVE_CSANDBOX:
        config = createSandboxConfig(cpython_restricted=False)
        def check_frame_not_restricted():
            frame = _getframe()
            assert frame.f_restricted == False
        Sandbox(config).call(check_frame_not_restricted)

    frame = _getframe()
    assert frame.f_restricted == False

def test_module_frame_restricted():
    from sys import _getframe

    config = createSandboxConfig(cpython_restricted=True)
    def check_module_restricted():
        restricted = _test_restricted(_getframe)
        assert restricted == True
    Sandbox(config).call(check_module_restricted)

    if HAVE_CSANDBOX:
        config = createSandboxConfig(cpython_restricted=False)
        def check_module_not_restricted():
            restricted = _test_restricted(_getframe)
            assert restricted == False
        Sandbox(config).call(check_module_not_restricted)

