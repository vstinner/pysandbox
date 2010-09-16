from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig
import readline
from optparse import OptionParser
from sandbox.version import VERSION
from sandbox import USE_CSANDBOX
import sys

class SandboxedInterpeter:
    def __init__(self):
        self.sandbox_locals = None
        self.config, self.options = self.parseOptions()

        self.config.enable('interpreter')
        if ('traceback' in self.config.features) \
        and (not self.config.cpython_restricted):
            self.config.allowPath(__file__)

        self.stdout = sys.stdout

    def parseOptions(self):
        parser = OptionParser(usage="%prog [options]")
        SandboxConfig.createOptparseOptions(parser,
            default_timeout=None)
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

        config = SandboxConfig.fromOptparseOptions(options)
        return config, options

    def dumpConfig(self):
        if self.options.verbose:
            from pprint import pprint
            print "Sandbox config:"
            pprint(self.config.__dict__)
        else:
            features = ', '.join(sorted(self.config.features))
            print "Enabled features: %s" % features
            if self.config.cpython_restricted:
                print "CPython restricted mode enabled."
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
        console = InteractiveConsole()
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
            import encodings
            import encodings.utf_8
            import encodings.utf_16_be
            import encodings.utf_32_be
            if sys.stdout.encoding:
                import codecs
                codecs.lookup(sys.stdout.encoding)
        sys.ps1 = '\nsandbox>>> '
        sys.ps2 = '.......... '
        sys.displayhook = self.displayhook
        sandbox = Sandbox(self.config)
        sandbox.call(self.interact)

if __name__ == "__main__":
    SandboxedInterpeter().main()
