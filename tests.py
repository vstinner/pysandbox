from __future__ import with_statement
from sandbox import Sandbox

def test_valid_code():
    """
    Check that a valid code works in the sandbox
    """
    with Sandbox():
        assert 1+2 == 3

def test_builtin_open():
    """
    Check that builtin open() is missing
    """
    filename = __file__
    try:
        with Sandbox():
            with open(filename) as fp:
                fp.read()
        assert False, "open is still available!"
    except NameError, err:
        # open() is blocked by the sandbox
        assert str(err) == "global name 'open' is not defined"

    # open() is restored at sandbox exit
    with open(filename) as fp:
        fp.read()

def test_closure():
    """
    Check that a function closure value can not be retrieved.
    """
    def get_cell_value(cell):
        # http://code.activestate.com/recipes/439096/
        return type(lambda: 0)((lambda x: lambda: x)(0).func_code, {}, None, None, (cell,))()

    with Sandbox():
        def closure(secret=42):
            def _closure():
                return secret
            return _closure
        func = closure()
        del closure
        try:
            cell = func.func_closure[0]
            secret = get_cell_value(cell)
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute 'func_closure'"
        else:
            assert secret == 42
            assert False, "func_closure attribute is present"

