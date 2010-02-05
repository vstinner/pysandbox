from __future__ import with_statement
import sys

options = {
    'import_whitelist': {
        'sys': ('argv',),
    },
}

def main():
    print "ARGV", sys.argv
    filename = sys.argv[1]
    from sandbox import Sandbox
    with open(filename, "rb") as fp:
        content = fp.read()
    del sys.argv[0]
    with Sandbox(**options):
        exec(content)

if __name__ == "__main__":
    main()
