from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig
import readline
from optparse import OptionParser

def createConfig():
    config = SandboxConfig()
    config.enable('interpreter')

    parser = OptionParser(usage="%prog [options]")
    config.createOptparseOptions(parser)
    options, argv = parser.parse_args()
    if argv:
        parser.print_help()
        exit(1)

    config.useOptparseOptions(options)
    return config

config = createConfig()
from pprint import pprint
print "Sandbox config:"
pprint(config.__dict__)
print

with Sandbox(config):
    InteractiveConsole().interact("Try to break the sandbox!")

