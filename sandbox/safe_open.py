from os.path import realpath
from .guard import guard
from .proxy import createObjectProxy
from errno import EACCES

def _safe_open(open_whitelist,
open_file=open, type=type, TypeError=TypeError,
any=any, realpath=realpath, guard=guard, ValueError=ValueError,
IOError=IOError, EACCES=EACCES):
    @guard(filename=str, mode=str, buffering=int)
    def safe_open(filename, mode='r', buffering=0):
        """A secure file reader."""

        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")

        realname = realpath(filename)
        if not any(realname.startswith(path) for path in open_whitelist):
            raise IOError(EACCES, "Sandbox deny access to the file %s" % filename)

        fileobj = open_file(filename, mode, buffering)

        return createObjectProxy(fileobj)
    return safe_open

