from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig, HAVE_PYPY
try:
    import readline
except ImportError:
    pass
from optparse import OptionParser
from sandbox.version import VERSION
import sys
from sys import version_info

def getEncoding():
    encoding = sys.stdin.encoding
    if encoding:
        return encoding
    # sys.stdin.encoding is None if stdin is not a tty

    # Emulate PYTHONIOENCODING on Python < 2.6
    import os
    env = os.getenv('PYTHONIOENCODING')
    if env:
        return env.split(':',1)[0]

    # Fallback to locales
    import locale
    return locale.getpreferredencoding()

ENCODING = getEncoding()

class SandboxConsole(InteractiveConsole):
    # Backport Python 2.6 fix for input encoding
    def raw_input(self, prompt):
        line = InteractiveConsole.raw_input(self, prompt)
        if not isinstance(line, unicode):
            line = line.decode(ENCODING)
        return line

class SandboxedInterpeter:
    def __init__(self):
        self.sandbox_locals = None
        self.options = self.parseOptions()
        self.config = self.createConfig()
        self.stdout = sys.stdout

    def parseOptions(self):
        parser = OptionParser(usage="%prog [options]")
        SandboxConfig.createOptparseOptions(parser, default_timeout=None)
        parser.add_option("--debug",
            help="Debug mode",
            action="store_true", default=False)
        parser.add_option("--verbose", "-v",
            help="Verbose mode",
            action="store_true", default=False)
        parser.add_option("--quiet", "-q",
            help="Quiet mode",
            action="store_true", default=False)
        options, argv = parser.parse_args()
        if argv:
            parser.print_help()
            exit(1)
        if options.quiet:
            options.verbose = False
        return options

    def createConfig(self):
        config = SandboxConfig.fromOptparseOptions(self.options)
        config.enable('traceback')
        config.enable('stdin')
        config.enable('stdout')
        config.enable('stderr')
        config.enable('exit')
        config.enable('site')
        config.enable('encodings')
        config._builtins_whitelist.add('compile')
        config.allowModuleSourceCode('code')
        config.allowModule('sys',
            'api_version', 'version', 'hexversion')
        config.allowSafeModule('sys', 'version_info')
        if HAVE_PYPY:
            config.enable('unicodedata')
            config.allowModule('os', 'write', 'waitpid')
            config.allowSafeModule('pyrepl', 'input')
            config.allowModule('pyrepl.keymap', 'compile_keymap', 'parse_keys')
        if self.options.debug:
            config.allowModule('sys', '_getframe')
            config.allowSafeModule('_sandbox', '_test_crash')
            config.allowModuleSourceCode('sandbox')
        if not config.cpython_restricted:
            config.allowPath(__file__)
        return config

    def dumpConfig(self):
        if self.options.debug:
            from pprint import pprint
            print "Sandbox config:"
            pprint(self.config.__dict__)
        else:
            features = ', '.join(sorted(self.config.features))
            print "Enabled features: %s" % features
            if self.config.cpython_restricted:
                print "CPython restricted mode enabled."
            if self.config.use_subprocess:
                text = "Run untrusted code in a subprocess"
                if self.options.debug:
                    from os import getpid
                    text += ": pid=%s" % getpid()
                print(text)
        if 'help' not in self.config.features:
            print "(use --features=help to enable the help function)"
        print

    def displayhook(self, result):
        if result is None:
            return
        self.sandbox_locals['_'] = result
        text = repr(result)
        if not self.options.quiet:
            print(text)
        else:
            self.stdout.write(text)

    def interact(self):
        console = SandboxConsole()
        self.sandbox_locals = console.locals
        if not self.options.quiet:
            banner = "Try to break the sandbox!"
        else:
            banner = ''
        console.interact(banner)

    def main(self):
        if not self.options.quiet:
            print("pysandbox %s" % VERSION)
            self.dumpConfig()
        if 'help' in self.config.features:
            # Import pydoc here because it uses a lot of modules
            # blocked by the sandbox
            import pydoc
        if self.config.cpython_restricted:
            # Import is blocked in restricted mode, so preload modules
            import codecs
            import encodings
            import encodings.utf_8
            import encodings.utf_16_be
            if version_info >= (2, 6):
                import encodings.utf_32_be
            if sys.stdout.encoding:
                codecs.lookup(sys.stdout.encoding)
            codecs.lookup(ENCODING)
        sys.ps1 = '\nsandbox>>> '
        sys.ps2 = '.......... '
        sys.displayhook = self.displayhook
        sandbox = Sandbox(self.config)
        sandbox.call(self.interact)

if __name__ == "__main__":
    SandboxedInterpeter().main()
