#!/usr/bin/env python
from __future__ import with_statement
from sandbox import Sandbox, SandboxError, SandboxConfig

def test_valid_code():
    with Sandbox():
        assert 1+2 == 3

from os.path import realpath
READ_FILENAME = realpath(__file__)
del realpath

def read_first_line(open):
    with open(READ_FILENAME) as fp:
        line = fp.readline()
    assert line.rstrip() == '#!/usr/bin/env python'

def test_open_whitelist():
    try:
        with Sandbox():
            read_first_line(open)
        assert False, "open whitelist doesn't work"
    except SandboxError, err:
        # Expect a safe_open() error
        assert str(err).startswith('Deny access to file ')

    config = SandboxConfig()
    config.open_whitelist.add(READ_FILENAME)
    with Sandbox(config):
        read_first_line(open)

    read_first_line(open)

def write_file(filename):
    with open(filename, "w") as fp:
        fp.write("test")

def test_write_file():
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile("wb") as tempfile:
        try:
            with Sandbox():
                write_file(tempfile.name)
            assert False, "writing to a file is not blocked"
        except ValueError, err:
            assert str(err) == "Only read modes are allowed."

    with NamedTemporaryFile("wb") as tempfile:
        write_file(tempfile.name)

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
            assert str(err) == 'Import "os" blocked by the sandbox'
        else:
            assert False

    # import is allowed outside the sandbox
    import os

    # sys.version is allowed by the sandbox
    import sys
    sys_version = sys.version
    del sys

    config = SandboxConfig()
    config.allowModule('sys', 'version')
    with Sandbox(config):
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

    try:
        exit()
    except SystemExit:
        pass
    else:
        assert False

def test_sytem_exit():
    with Sandbox():
        try:
            raise SystemExit()
        except NameError, err:
            assert str(err) == "global name 'SystemExit' is not defined"
        except:
            assert False

    try:
        raise SystemExit()
    except SystemExit:
        pass
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

def get_import_from_func_locals(safe_import, exc_info):
    try:
        safe_import("os")
    except ImportError:
        # import os always raise an error
        err_value, err_type, try_traceback = exc_info()
        safe_import_traceback = try_traceback.tb_next
        safe_import_frame = safe_import_traceback.tb_frame
        return safe_import_frame.f_locals['__import__']

def test_func_locals():
    import sys

    with Sandbox():
        try:
            get_import_from_func_locals(__import__, sys.exc_info)
        except AttributeError, err:
            assert str(err) == "'frame' object has no attribute 'f_locals'"
        else:
            assert False

    builtin_import = __import__
    from sandbox.safe_import import _safe_import
    safe_import = _safe_import(builtin_import, {})
    myimport = get_import_from_func_locals(safe_import, sys.exc_info)
    assert myimport is builtin_import

def get_file_from_subclasses():
    for subtype in object.__subclasses__():
        if subtype.__name__ == "file":
            return subtype
    raise ValueError("Unable to get file type")

def test_subclasses():
    with Sandbox():
        try:
            get_file_from_subclasses()
        except AttributeError, err:
            assert str(err) == "type object 'object' has no attribute '__subclasses__'"
        else:
            assert False

    file = get_file_from_subclasses()
    read_first_line(file)

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

