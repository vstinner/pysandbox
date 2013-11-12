from sandbox import HAVE_PYPY, SandboxError, Sandbox
from sandbox.test import createSandbox, createSandboxConfig, SkipTest

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

def test_frame_locals():
    def func_secret_local(callback):
        secret = 9
        return callback()

    def get_func_locals():
        import sys
        frame = sys._getframe(1)
        return frame.f_locals['secret']

    def get_secret():
        return func_secret_local(get_func_locals)

    import sys

    def test_get_secret():
        try:
            get_secret()
        except AttributeError, err:
            assert str(err) == "'frame' object has no attribute 'f_locals'"
        else:
            assert False
    createSandbox('debug_sandbox').call(test_get_secret)

    assert get_secret() == 9

def test_frame_globals():
    global TEST_FRAME_GLOBALS_SECRET
    TEST_FRAME_GLOBALS_SECRET = 44

    def get_secret():
        import sys
        frame = sys._getframe()
        return frame.f_globals.get('TEST_FRAME_GLOBALS_SECRET')

    def test_get_secret():
        try:
            get_secret()
        except AttributeError, err:
            assert str(err) == "'frame' object has no attribute 'f_globals'"
        else:
            assert False

    # traceback: want frame.f_back
    config = createSandboxConfig()
    config.allowModule('sys', '_getframe')
    Sandbox(config).call(test_get_secret)

    assert get_secret() == 44

def test_traceback_frame():
    global TEST_TRACEBACK_FRAME_SECRET
    TEST_TRACEBACK_FRAME_SECRET = 8

    def get_secret():
        def get_frame_secret(frame):
            while frame.f_back is not None:
                value = frame.f_globals.get('TEST_TRACEBACK_FRAME_SECRET')
                if value is not None:
                    return value
                frame = frame.f_back

        class CM:
            def __init__(self):
                self.secret = None

            def __enter__(self):
                return self

            def __exit__(self, exc_value, exc_type, traceback):
                self.secret = get_frame_secret(traceback.tb_frame)
                return True

        cm = CM()
        with cm:
            raise ValueError()
        return cm.secret

    def test_get_secret():
        try:
            get_secret()
        except AttributeError, err:
            assert str(err) == "'traceback' object has no attribute 'tb_frame'"
        else:
            assert False
    config = createSandboxConfig()
    config.allowModule('sys', '_getframe')
    Sandbox(config).call(test_get_secret)

    assert get_secret() == 8

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

