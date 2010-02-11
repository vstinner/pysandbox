from os.path import realpath
from sandbox import SandboxError
from .guard import guard
from .proxy import createObjectProxy

def _safe_open(open_whitelist,
open_file=open, type=type, TypeError=TypeError,
any=any, realpath=realpath, guard=guard, ValueError=ValueError,
SandboxError=SandboxError):
    @guard(filename=str, mode=str, buffering=int)
    def safe_open(filename, mode='r', buffering=0):
        """A secure file reader."""

        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")

        # Try to open the file before checking the path whitelist
        # to raise an exception if the file doesn't exist
        fileobj = open_file(filename, mode, buffering)

        realname = realpath(filename)
        if not any(realname.startswith(path) for path in open_whitelist):
            raise SandboxError("Deny access to file %s" % filename)

        return createObjectProxy(fileobj)
    return safe_open

