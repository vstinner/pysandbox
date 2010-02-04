from __future__ import with_statement
from sandbox import Sandbox, SandboxError
from tempfile import NamedTemporaryFile
from os.path import realpath

def test_valid_code():
    with Sandbox():
        assert 1+2 == 3

def test_open_whitelist():
    filename = realpath(__file__)

    try:
        with Sandbox(open_whitelist=tuple()):
            with open(filename) as fp:
                fp.read()
        assert False, "open whitelist doesn't work"
    except SandboxError, err:
        # Expect a safe_open() error
        assert str(err).startswith('Deny access to file ')

    with Sandbox(open_whitelist=[filename]):
        with open(filename) as fp:
            fp.read()

    with open(filename) as fp:
        fp.read()

def test_write_file():
    with NamedTemporaryFile("wb") as tempfile:
        try:
            with Sandbox():
                with open(tempfile.name, "w") as fp:
                    fp.write("test")
            assert False, "writing to a file is not blocked"
        except ValueError, err:
            # Expect a safe_open() error
            assert str(err) == "Only read modes are allowed."

    # open() is restored at sandbox exit
    with NamedTemporaryFile("wb") as tempfile:
        with open(tempfile.name, "w") as fp:
            fp.write("test")

def read_closure_secret():
    def get_cell_value(cell):
        # http://code.activestate.com/recipes/439096/
        return type(lambda: 0)((lambda x: lambda: x)(0).func_code, {}, None, None, (cell,))()

    def closure(secret=42):
        def _closure():
            return secret
        return _closure
    func = closure()
    del closure
    try:
        cell = func.func_closure[0]
    except AttributeError:
        # Python 2.6+
        cell = func.__closure__[0]
    secret = get_cell_value(cell)
    assert secret == 42

def test_closure():
    with Sandbox():
        try:
            read_closure_secret()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__closure__'"
        else:
            assert False, "func_closure is present"

    # closure are readable outside the sandbox
    read_closure_secret()

def test_import():
    with Sandbox():
        try:
            import os
        except ImportError, err:
            assert str(err) == 'Import os blocked by the sandbox'
        else:
            assert False

    # import is allowed outside the sandbox
    import os

    # sys.version is allowed by the sandbox
    import sys
    sys_version = sys.version
    del sys
    with Sandbox():
        import sys
        assert sys.__name__ == 'sys'
        assert sys.version == sys_version

def test_exit():
    with Sandbox():
        try:
            exit()
        except SandboxError, err:
            assert str(err) == "Function exit() blocked by the sandbox"
        else:
            assert False

def get_sandbox_from_func_globals():
    def mysum(a, b):
        return a+b
    try:
        func_globals = mysum.func_globals
    except AttributeError:
        # Python 2.6+
        func_globals = mysum.__globals__
    return func_globals['Sandbox']

def test_func_globals():
    with Sandbox():
        try:
            get_sandbox_from_func_globals()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__globals__'"
        else:
            assert False

    assert get_sandbox_from_func_globals() is Sandbox

def main():
    # Get all tests
    all_tests = []
    _locals = globals().items()
    for name, value in _locals:
        if not name.startswith("test"):
            continue
        all_tests.append(value)

    # Run tests
    nerror = 0
    for func in all_tests:
        name = func.__name__
        try:
            func()
        except BaseException, err:
            nerror += 1
            print "Test %s: FAILED! %r" % (name, err)
        else:
            print "Test %s: ok" % name

    # Exit
    from sys import exit
    print
    if nerror:
        print "%s ERRORS!" % nerror
        exit(1)
    else:
        print "All tests succeed"
        exit(0)

if __name__ == "__main__":
    main()

