from __future__ import with_statement
import sys
from sandbox import Sandbox, SandboxConfig
from optparse import OptionParser

def parseOptions():

    parser = OptionParser(usage="%prog [options] -- script.py [script options] [arg1 arg2 ...]")
    SandboxConfig.createOptparseOptions(parser)
    options, argv = parser.parse_args()
    if not argv:
        parser.print_help()
        exit(1)

    config = SandboxConfig.fromOptparseOptions(options)
    return config, argv

def main():
    config, argv = parseOptions()
    config.allowModule('sys', 'argv')

    with open(argv[0], "rb") as fp:
        content = fp.read()

    sys.argv = list(argv)
    with Sandbox(config):
        exec content in {'__builtins__': __builtins__}

if __name__ == "__main__":
    main()
