from sandbox import Sandbox, HAVE_CPYTHON_RESTRICTED, HAVE_CSANDBOX
from sandbox.test import SkipTest, createSandboxConfig

def _test_restricted(_getframe):
    frame =  _getframe()
    return frame.f_restricted

def test_frame_restricted():
    if not HAVE_CPYTHON_RESTRICTED:
        raise SkipTest("restricted mode is specific to Python 2.x")
    if not HAVE_CSANDBOX:
        raise SkipTest("require _sandbox")

    from sys import _getframe

    config = createSandboxConfig(cpython_restricted=True)
    def check_frame_restricted():
        frame = _getframe()
        assert frame.f_restricted == True
    Sandbox(config).call(check_frame_restricted)

    config = createSandboxConfig(cpython_restricted=False)
    def check_frame_not_restricted():
        frame = _getframe()
        assert frame.f_restricted == False
    Sandbox(config).call(check_frame_not_restricted)

    frame = _getframe()
    assert frame.f_restricted == False

def test_module_frame_restricted():
    if not HAVE_CPYTHON_RESTRICTED:
        raise SkipTest("restricted mode is specific to Python 2.x")
    if not HAVE_CSANDBOX:
        raise SkipTest("require _sandbox")

    from sys import _getframe

    config = createSandboxConfig(cpython_restricted=True)
    def check_module_restricted():
        restricted = _test_restricted(_getframe)
        assert restricted == True
    Sandbox(config).call(check_module_restricted)

    config = createSandboxConfig(cpython_restricted=False)
    def check_module_not_restricted():
        restricted = _test_restricted(_getframe)
        assert restricted == False
    Sandbox(config).call(check_module_not_restricted)

