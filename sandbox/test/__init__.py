from sandbox import Sandbox, SandboxConfig
from functools import wraps

class TestException(Exception):
    pass

class SkipTest(Exception):
    pass

def createSandboxConfig(*features, **kw):
    if createSandboxConfig.debug:
        features += ("stdout", "stderr")
    return SandboxConfig(*features, **kw)
createSandboxConfig.debug = False

def createSandbox(*features):
    config = createSandboxConfig(*features)
    return Sandbox(config)

def skipIf(test, reason):
    """
    Raise SkipTest(reason) if test is True.

    Example:

    @skipIf(1==2, 'something is broken')
    def test_sum():
        assert 1+1 == 2
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            if test:
                raise SkipTest(reason)
            return func(*args, **kw)
        return wrapper
    return decorator

