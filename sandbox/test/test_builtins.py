from sandbox import Sandbox, SandboxError, HAVE_CSANDBOX, HAVE_PYPY
from sandbox.test import SkipTest, createSandbox, createSandboxConfig, unindent
from sys import version_info

def test_call_exec_builtins():
    code = unindent('''
        result = []
        exec "result.append(type(__builtins__))" in {'result': result}
        builtin_type = result[0]
        assert builtin_type != dict
    ''')
    config = createSandboxConfig()
    if HAVE_PYPY:
        # FIXME: is it really needed?
        config._builtins_whitelist.add('compile')
    Sandbox(config).execute(code)

def test_exec_builtins():
    config = createSandboxConfig()
    Sandbox(config).execute("""
assert type(__builtins__) != dict
    """.strip())

def test_builtins_setitem():
    code = unindent('''
        def builtins_superglobal():
            if isinstance(__builtins__, dict):
                __builtins__['SUPERGLOBAL'] = 42
                assert SUPERGLOBAL == 42
                del __builtins__['SUPERGLOBAL']
            else:
                __builtins__.SUPERGLOBAL = 42
                assert SUPERGLOBAL == 42
                del __builtins__.SUPERGLOBAL
    ''')

    unsafe_code = code + unindent('''
        try:
            builtins_superglobal()
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False
    ''')
    createSandbox().execute(unsafe_code)

    safe_code = code + unindent('''
        builtins_superglobal()
    ''')
    execute_code(safe_code)

def test_builtins_init():
    import warnings

    code = unindent('''
        def check_init():
            __builtins__.__init__({})

        def check_dict_init():
            try:
                dict.__init__(__builtins__, {})
            except ImportError, err:
                assert str(err) == 'Import "_warnings" blocked by the sandbox'
            except DeprecationWarning, err:
                assert str(err) == 'object.__init__() takes no parameters'
            else:
                assert False
    ''')

    unsafe_code = code + unindent('''
        check_init()
    ''')

    try:
        createSandbox().execute(unsafe_code)
    except SandboxError, err:
        assert str(err) == "Read only object", str(err)
    else:
        assert False

    # FIXME: is this test still needed?
    # if version_info >= (2, 6):
    #     original_filters = warnings.filters[:]
    #     try:
    #         warnings.filterwarnings('error', '', DeprecationWarning)

    #         config = createSandboxConfig()
    #         Sandbox(config).call(check_dict_init)
    #     finally:
    #         del warnings.filters[:]
    #         warnings.filters.extend(original_filters)

def test_modify_builtins_dict():
    code = unindent('''
        def builtins_dict_superglobal():
            __builtins__['SUPERGLOBAL'] = 42
            assert SUPERGLOBAL == 42
            del __builtins__['SUPERGLOBAL']
    ''')

    unsafe_code = code + unindent('''
        try:
            builtins_dict_superglobal()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__setitem__'"
        else:
            assert False
    ''')
    try:
        createSandbox().execute(unsafe_code)
    except SandboxError, err:
        assert str(err) == "Read only object"

def test_del_builtin():
    code = unindent('''
        def del_builtin_import():
            import_func = __builtins__['__import__']
            dict.__delitem__(__builtins__, '__import__')
            try:
                try:
                    import sys
                except NameError, err:
                    assert str(err) == "type object 'dict' has no attribute '__setitem__'"
            finally:
                __builtins__['__import__'] = import_func
    ''')

    unsafe_code = code + unindent('''
        try:
            del_builtin_import()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__delitem__'"
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False
    ''')

    config = createSandboxConfig()
    config.allowModule('sys')
    Sandbox(config).execute(unsafe_code)

