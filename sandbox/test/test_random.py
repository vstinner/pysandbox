from sandbox import Sandbox
from sandbox.test import createSandboxConfig, SkipTest

def test_random():
    config = createSandboxConfig('random')
    if config.cpython_restricted:
        raise SkipTest("deny importing modules")

    check_random = 'import random; random.randint(1, 6)'

    Sandbox(config).execute(check_random)

