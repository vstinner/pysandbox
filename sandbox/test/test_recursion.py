from sandbox import Sandbox
from sandbox.test import createSandboxConfig
import math

def test_recusion():
    def factorial(n):
        if n >= 2:
            return n * factorial(n - 1)
        else:
            return 1

    config = createSandboxConfig()
    max_frames = config.recusion_limit + 1
    try:
        Sandbox(config).call(factorial, max_frames)
    except RuntimeError, err:
        assert str(err) == 'maximum recursion depth exceeded'
    else:
        assert False

    assert factorial(max_frames) == math.factorial(max_frames)

