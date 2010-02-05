from __future__ import with_statement
import sys
from sandbox import Sandbox, SandboxConfig
from optparse import OptionParser

options = {
    'import_whitelist': {
        'sys': ('argv',),
    },
}

def parseOptions():
    parser = OptionParser(usage="%prog [options] -- script.py [arg1 arg2 ...]")
    parser.add_option("--features", help="List of enabled features separated by a comma",
        type="str")
    options, argv = parser.parse_args()
    if not argv:
        parser.print_help()
        exit(1)
    return argv, options

def main():
    argv, options = parseOptions()

    with open(argv[0], "rb") as fp:
        content = fp.read()

    config = SandboxConfig()
    config.useOptparseOptions(options)
    sys.argv = list(argv)
    with Sandbox(config):
        exec(content)

if __name__ == "__main__":
    main()
