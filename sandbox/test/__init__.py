from sandbox import Sandbox, SandboxConfig

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

