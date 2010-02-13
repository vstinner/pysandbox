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
        config = SandboxConfig()

        parser = OptionParser(usage="%prog [options]")
        config.createOptparseOptions(parser)
        parser.add_option("--verbose", "-v", help="Verbose mode",
            action="store_true", default=False)
        options, argv = parser.parse_args()
        if argv:
            parser.print_help()
            exit(1)

        config.useOptparseOptions(options)
        return config, options

    def dumpConfig(self):
        if self.options.verbose:
            from pprint import pprint
            print "Sandbox config:"
            pprint(self.config.__dict__)
        else:
            print "Enabled features: %s" % ', '.join(sorted(self.config.features))
        print

    def main(self):
        self.dumpConfig()
        with Sandbox(self.config):
            InteractiveConsole().interact("Try to break the sandbox!")

if __name__ == "__main__":
    SandboxedInterpeter().main()
