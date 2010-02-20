from __future__ import with_statement
from .config import SandboxConfig
from .proxy import proxy
from .blacklist_proxy import createDictProxy

def keywordsProxy(keywords):
    return dict(
        (key, proxy(value))
        for key, value in keywords.iteritems())

class Sandbox:
    PROTECTIONS = []

    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = SandboxConfig()
        self.protections = [protection() for protection in self.PROTECTIONS]

    def __enter__(self):
        for protection in self.protections:
            protection.enable(self)

    def __exit__(self, type, value, traceback):
        for protection in reversed(self.protections):
            protection.disable(self)

    def call(self, func, *args, **kw):
        """
        Call a function in the sandbox.
        """
        args = proxy(args)
        kw = keywordsProxy(kw)
        with self:
            func(*args, **kw)

    def execute(self, code, globals=None, locals=None):
        """
        execute the code in the sandbox:

           exec code in globals, locals
        """
        if globals is not None:
            globals = createDictProxy(globals)
        if locals is not None:
            locals = createDictProxy(locals)
        with self:
            exec code in globals, locals

    def createCallback(self, func, *args, **kw):
        """
        Create a callback: the function will be called in the sandbox.
        The callback takes no argument.
        """
        args = proxy(args)
        kw = keywordsProxy(kw)
        print kw
        sandbox = self
        def callback():
            with sandbox:
                func(*args, **kw)
        return callback

