from sandbox import HAVE_PYPY, SandboxError
from sandbox.test import createSandbox, SkipTest, unindent, execute_code

# FIXME: reenable these tests
if HAVE_PYPY:
    raise SkipTest("tests disabled on PyPy")

def test_closure():
    code = unindent('''
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
    ''')

    # Begin by a test outside the sandbox to fill the type cache
    unsafe_code = code + unindent('''
        try:
            read_closure_secret()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__closure__'"
        else:
            assert False, "func_closure is present"
    ''')
    createSandbox().execute(unsafe_code)

    # Repeat the test to ensure that the attribute cache is cleared correctly
    safe_code = code + unindent('''
        read_closure_secret()
    ''')
    execute_code(safe_code)


def test_func_globals():
    code = unindent('''
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
    ''')

    unsafe_code = code + unindent('''
        try:
            get_secret_from_func_globals()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__globals__'"
        else:
            assert False
    ''')
    createSandbox().execute(unsafe_code)

    safe_code = code + unindent("""
        assert get_secret_from_func_globals() == 42
    """)
    execute_code(safe_code)


def test_func_locals():
    # FIXME: rewrite test with a simpler trace, without safe_import
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
    # FIXME: use sandbox.execute()
    createSandbox().call(frame_locals_denied)

    builtin_import = __import__
    from sandbox.safe_import import _safe_import
    safe_import = _safe_import(builtin_import, {})
    myimport = get_import_from_func_locals(safe_import, sys.exc_info)
    assert myimport is builtin_import


def test_func_defaults():
    from sys import version_info
    if version_info < (2, 6):
        raise SkipTest("tests disabled on Python < 2.6")

    unsafe_code = unindent('''
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
    ''')

    if version_info < (3, 0):
        unsafe_code += unindent('''
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
        ''')

    sandbox = createSandbox()
    sandbox.execute(unsafe_code)


def test_type_bases():
    from sys import version_info
    if version_info < (2, 6):
        raise SkipTest("tests disabled on Python < 2.6")

    code = unindent('''
    def test():
        class A(object):
            pass
        class B(object):
            pass
        class X(A):
            pass
        X.__bases__ = (B,)
        if not issubclass(X, B):
            raise AttributeError("__bases__ error")
    ''')

    unsafe_code = code + unindent('''
        try:
            test()
        except AttributeError, err:
            assert str(err) == "__bases__ error"
        else:
            assert False
    ''')
    createSandbox().execute(unsafe_code)

    safe_code = code + unindent('''
        test()
    ''')
    execute_code(safe_code)

