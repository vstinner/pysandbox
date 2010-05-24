from __future__ import with_statement
from .config import SandboxConfig
from .proxy import proxy
from .blacklist_proxy import createDictProxy
from .timeout import limitedTime

def keywordsProxy(keywords):
    # Dont proxy keys because function keywords must be strings
    return dict(
        (key, proxy(value))
        for key, value in keywords.iteritems())

def _call_exec(code, globals, locals):
    exec code in globals, locals

class Sandbox:
    PROTECTIONS = []

    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = SandboxConfig()
        self.protections = [protection() for protection in self.PROTECTIONS]

    def _enable(self):
        for protection in self.protections:
            protection.enable(self)

    def _disable(self):
        for protection in reversed(self.protections):
            protection.disable(self)

    def _call(self, func, args, kw):
        timeout = self.config.timeout
        self._enable()
        try:
            if timeout is not None:
                return limitedTime(timeout, func, *args, **kw)
            else:
                return func(*args, **kw)
        finally:
            self._disable()

    def call(self, func, *args, **kw):
        """
        Call a function in the sandbox.
        """
        args = proxy(args)
        kw = keywordsProxy(kw)
        return self._call(func, args, kw)

    def execute(self, code, globals=None, locals=None):
        """
        execute the code in the sandbox:

           exec code in globals, locals

        Use globals={} by default to get an empty namespace.
        """
        if globals is not None:
            globals = createDictProxy(globals)
        else:
            globals = {}
        if locals is not None:
            locals = createDictProxy(locals)

        self._call(_call_exec, (code, globals, locals), {})

    def createCallback(self, func, *args, **kw):
        """
        Create a callback: the function will be called in the sandbox.
        The callback takes no argument.
        """
        args = proxy(args)
        kw = keywordsProxy(kw)
        def callback():
            return self._call(func, args, kw)
        return callback

