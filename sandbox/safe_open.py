from os.path import realpath, exists
from sandbox import SandboxError

def _safe_open(open, open_whitelist):
    """
    Open a file a for reading. If the open_whitelist is defined (not None):
    check that the file name starts with one of the path of open_whitelist,
    otherwise raise a SandboxError.
    """
    def safe_open(filename, mode='r', buffering=0):
        if mode not in ['r', 'rb', 'rU']:
            raise ValueError("Only read modes are allowed.")
        fp = open(filename, mode, buffering)
        if open_whitelist is not None:
            realname = realpath(filename)
            if not any(realname.startswith(path) for path in open_whitelist):
                fp.close()
                raise SandboxError("Deny access to file %s" % filename)
        return fp
    return safe_open

