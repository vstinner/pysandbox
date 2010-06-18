from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig
import readline
from optparse import OptionParser

class SandboxedInterpeter:
    def __init__(self):
        self.config, self.options = self.parseOptions()

        self.config.enable('interpreter')
        if 'traceback' in self.config.features:
            self.config.allowPath(__file__)

    def parseOptions(self):
        parser = OptionParser(usage="%prog [options]")
        SandboxConfig.createOptparseOptions(parser,
            default_timeout=None)
        parser.add_option("--verbose", "-v",
            help="Verbose mode",
            action="store_true", default=False)
        options, argv = parser.parse_args()
        if argv:
            parser.print_help()
            exit(1)

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
            print "CPython restricted mode enabled."
        if 'help' not in self.config.features:
            print "(use --features=help to enable the help function)"
        print

    def interact(self):
        InteractiveConsole().interact("Try to break the sandbox!")

    def main(self):
        self.dumpConfig()
        if 'help' in self.config.features:
            # Import pydoc here because it uses a lot of modules
            # blocked by the sandbox
            import pydoc
        import sys
        sys.ps1 = '\nsandbox>>> '
        sys.ps2 = '.......... '
        sandbox = Sandbox(self.config)
        sandbox.call(self.interact)

if __name__ == "__main__":
    SandboxedInterpeter().main()
