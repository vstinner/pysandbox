import sys
from sandbox import SandboxError

def createNoAttribute(stream_name):
    def _blocked(name):
        raise SandboxError("Block access to sys.%s.%s" % (stream_name, name))

    # FIXME:
    #class NoAttribute(object):
    #    __slots__ = tuple()
    class NoAttribute:
        def __getattr__(self, name):
            _blocked(name)

        def __setattr__(self, name, value):
            _blocked(name)

        def __delattr__(self, name):
            _blocked(name)
    return NoAttribute()

class ProtectStdio:
    """
    If stdin / stdout / stderr feature is disable, replace sys.stdin /
    sys.stdout / sys.stderr by a dummy object with no attribute.
    """
    def __init__(self):
        self.sys = sys

    def enable(self, sandbox):
        features = sandbox.config.features

        self.stdin = self.sys.stdin
        if 'stdin' not in features:
            self.sys.stdin = createNoAttribute("stdin")

        self.stdout = self.sys.stdout
        if 'stdout' not in features:
            self.sys.stdout = createNoAttribute("stdout")

        self.stderr = self.sys.stderr
        if 'stderr' not in features:
            self.sys.stderr = createNoAttribute("stderr")

    def disable(self, sandbox):
        self.sys.stdin = self.stdin
        self.sys.stdout = self.stdout
        self.sys.stderr = self.stderr

