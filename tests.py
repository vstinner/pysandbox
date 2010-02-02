from __future__ import with_statement
from sandbox import Sandbox, SandboxError
from tempfile import NamedTemporaryFile

def test_valid_code():
    with Sandbox():
        assert 1+2 == 3

def test_open_whitelist():
    filename = __file__

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
    cell = func.func_closure[0]
    secret = get_cell_value(cell)
    assert secret == 42

def test_closure():
    with Sandbox():
        try:
            read_closure_secret()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute 'func_closure'"
        else:
            assert False, "func_closure is present"

    # closure are readable outside the sandbox
    read_closure_secret()

def test_import():
    with Sandbox():
        try:
            import os
        except ImportError, err:
            assert str(err) == 'Deny import in the sandbox'
        else:
            assert False

    # import is allowed outside the sandbox
    import os

