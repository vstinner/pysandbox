from os.path import realpath
from .proxy import createReadOnlyObject
from errno import EACCES

def _safe_open(open_whitelist):
    open_file = open
    def safe_open(filename, mode='r', buffering=0):
        """A secure file reader."""
        if type(mode) is not str:
            raise TypeError("mode have to be a string, not %s" % type(name).__name__)
        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")

        realname = realpath(filename)
        if not any(realname.startswith(path) for path in open_whitelist):
            raise IOError(EACCES, "Sandbox deny access to the file %s" % repr(filename))

        fileobj = open_file(filename, mode, buffering)
        return createReadOnlyObject(fileobj)
    return safe_open

