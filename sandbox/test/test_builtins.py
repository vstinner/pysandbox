from sandbox import Sandbox, SandboxError, HAVE_CSANDBOX, HAVE_PYPY
from sandbox.test import SkipTest, createSandbox, createSandboxConfig
from sys import version_info

def test_exec_builtins():
    def check_builtins_type():
        result = []
        exec "result.append(type(__builtins__))" in {'result': result}
        builtin_type = result[0]
        assert builtin_type != dict
    config = createSandboxConfig()
    if HAVE_PYPY:
        # FIXME: is it really needed?
        config._builtins_whitelist.add('compile')
    Sandbox(config).call(check_builtins_type)

def test_builtins_setitem():
    def builtins_superglobal():
        if isinstance(__builtins__, dict):
            __builtins__['SUPERGLOBAL'] = 42
            assert SUPERGLOBAL == 42
            del __builtins__['SUPERGLOBAL']
        else:
            __builtins__.SUPERGLOBAL = 42
            assert SUPERGLOBAL == 42
            del __builtins__.SUPERGLOBAL

    def readonly_builtins():
        try:
            builtins_superglobal()
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False
    createSandbox().call(readonly_builtins)

    builtins_superglobal()

def test_builtins_init():
    import warnings

    def check_init():
        try:
            __builtins__.__init__({})
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False

    def check_dict_init():
        try:
            dict.__init__(__builtins__, {})
        except ImportError, err:
            assert str(err) == 'Import "_warnings" blocked by the sandbox'
        except DeprecationWarning, err:
            assert str(err) == 'object.__init__() takes no parameters'
        else:
            assert False

    createSandbox().call(check_init)

    if version_info >= (2, 6):
        original_filters = warnings.filters[:]
        try:
            warnings.filterwarnings('error', '', DeprecationWarning)

            config = createSandboxConfig()
            Sandbox(config).call(check_dict_init)
        finally:
            del warnings.filters[:]
            warnings.filters.extend(original_filters)

def test_modify_builtins_dict():
    def builtins_dict_superglobal():
        __builtins__['SUPERGLOBAL'] = 42
        assert SUPERGLOBAL == 42
        del __builtins__['SUPERGLOBAL']

    def readonly_builtins_dict():
        try:
            builtins_dict_superglobal()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__setitem__'"
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False
    createSandbox().call(readonly_builtins_dict)

def test_del_builtin():
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

    def del_builtin_denied():
        try:
            del_builtin_import()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__delitem__'"
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False

    config = createSandboxConfig()
    config.allowModule('sys')
    Sandbox(config).call(del_builtin_denied)

