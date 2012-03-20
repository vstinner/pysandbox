from __future__ import absolute_import
from os.path import realpath
from .proxy import createReadOnlyObject
from errno import EACCES

def _safe_open(open_whitelist):
    open_file = open
    # Python3 has extra options like encoding and newline
    def safe_open(filename, mode='r', buffering=-1, **kw):
        """A secure file reader."""
        if type(mode) is not str:
            raise TypeError("mode have to be a string, not %s" % type(mode).__name__)
        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")

        realname = realpath(filename)
        if not any(realname.startswith(path) for path in open_whitelist):
            raise IOError(EACCES, "Sandbox deny access to the file %s" % repr(filename))

        fileobj = open_file(filename, mode, buffering, **kw)
        return createReadOnlyObject(fileobj)
    return safe_open

