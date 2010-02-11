from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig
import readline
from optparse import OptionParser

def createConfig():
    config = SandboxConfig('interpreter')

    parser = OptionParser(usage="%prog [options]")
    config.createOptparseOptions(parser)
    parser.add_option("--verbose", "-v", help="Verbose mode",
        action="store_true", default=False)
    options, argv = parser.parse_args()
    if argv:
        parser.print_help()
        exit(1)

    config.useOptparseOptions(options)
    if 'traceback' in config.features:
        config.allowPath(__file__)

    if options.verbose:
        from pprint import pprint
        print "Sandbox config:"
        pprint(config.__dict__)
    else:
        print "Enabled features: %s" % ', '.join(sorted(config.features))
    print

    return config

config = createConfig()
with Sandbox(config):
    InteractiveConsole().interact("Try to break the sandbox!")

