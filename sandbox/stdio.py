import sys
from sandbox import SandboxError

def createNoWrite(name):
    def _blocked():
        raise SandboxError("Block access to sys.%s" % name)

    class NoWrite:
        def __getattr__(self, name):
            _blocked()

        def __setattr__(self, name, value):
            _blocked()

        def __delattr__(self, name):
            _blocked()
    return NoWrite()

class ProtectStdio:
    """
    Hide unsafe frame attributes from the Python space:
     * frame.xxx
     * function.xxx
    """
    def __init__(self):
        self.sys = sys

    def enable(self, sandbox):
        features = sandbox.config.features

        self.stdin = self.sys.stdin
        if 'stdin' not in features:
            self.sys.stdin = createNoWrite("stdin") 

        self.stdout = self.sys.stdout
        if 'stdout' not in features:
            self.sys.stdout = createNoWrite("stdout") 

        self.stderr = self.sys.stderr
        if 'stderr' not in features:
            self.sys.stderr = createNoWrite("stderr") 

    def disable(self, sandbox):
        self.sys.stdin = self.stdin
        self.sys.stdout = self.stdout
        self.sys.stderr = self.stderr

