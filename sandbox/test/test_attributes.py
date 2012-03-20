from sandbox import HAVE_PYPY, SandboxError
from sandbox.test import createSandbox, SkipTest

# FIXME: reenable these tests
if HAVE_PYPY:
    raise SkipTest("tests disabled on PyPy")

SECRET = 42

def get_secret_from_func_globals():
    def mysum(a, b):
        return a+b
    try:
        func_globals = mysum.func_globals
    except AttributeError:
        # Python 2.6+
        func_globals = mysum.__globals__
    return func_globals['SECRET']

def test_closure():
    def read_closure_secret():
        def createClosure(secret):
            def closure():
                return secret
            return closure
        func = createClosure(42)
        try:
            cell = func.func_closure[0]
        except AttributeError:
            # Python 2.6+
            cell = func.__closure__[0]
        # Does Python < 2.5 have the cell_contents attribute?  See this recipe,
        # get_cell_value(), for version without the attribute:
        # http://code.activestate.com/recipes/439096/
        secret = cell.cell_contents
        assert secret == 42

    def check_closure():
        try:
            read_closure_secret()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__closure__'"
        else:
            assert False, "func_closure is present"

    # Begin by a test outside the sandbox to fill the type cache
    read_closure_secret()
    createSandbox().call(check_closure)

    # Repeat the test to ensure that the attribute cache is cleared correctly
    read_closure_secret()
    createSandbox().call(check_closure)

def test_func_globals():
    def func_globals_denied():
        try:
            get_secret_from_func_globals()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__globals__'"
        else:
            assert False
    createSandbox().call(func_globals_denied)

    assert get_secret_from_func_globals() == 42

def test_func_locals():
    def get_import_from_func_locals(safe_import, exc_info):
        try:
            safe_import("os")
        except ImportError:
            # import os always raise an error
            err_value, err_type, try_traceback = exc_info()
            safe_import_traceback = try_traceback.tb_next
            safe_import_frame = safe_import_traceback.tb_frame
            return safe_import_frame.f_locals['__import__']

    import sys

    def frame_locals_denied():
        try:
            get_import_from_func_locals(__import__, sys.exc_info)
        except AttributeError, err:
            assert str(err) == "'frame' object has no attribute 'f_locals'"
        else:
            assert False
    createSandbox().call(frame_locals_denied)

    builtin_import = __import__
    from sandbox.safe_import import _safe_import
    safe_import = _safe_import(builtin_import, {})
    myimport = get_import_from_func_locals(safe_import, sys.exc_info)
    assert myimport is builtin_import

def test_func_defaults():
    from sys import version_info

    def func_defaults_denied():
        if version_info < (3, 0):
            try:
                open.func_defaults
            except AttributeError, err:
                assert str(err) in (
                    # open is safe_open()
                    "'function' object has no attribute 'func_defaults'",
                    # builtin open() in restricted mode
                    "'builtin_function_or_method' object has no attribute 'func_defaults'",
                )
            else:
                assert False
        if version_info >= (2, 6):
            try:
                open.__defaults__
            except AttributeError, err:
                assert str(err) in (
                    # open is safe_open()
                    "'function' object has no attribute '__defaults__'",
                    # builtin open() in restricted mode
                    "'builtin_function_or_method' object has no attribute '__defaults__'",
                )
            else:
                assert False
    createSandbox().call(func_defaults_denied)

def test_type_bases():
    from sys import version_info
    if version_info < (2, 6):
        raise SkipTest("tests disabled on Python < 2.6")

    def test():
        class A(object):
            pass
        class B(object):
            pass
        class X(A):
            pass
        X.__bases__ = (B,)
        if not issubclass(X, B):
            raise SandboxError("yep")

    def sandbox_test():
        try:
            test()
        except SandboxError:
            pass
        else:
            assert False

    createSandbox().call(sandbox_test)

    test()

