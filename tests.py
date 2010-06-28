#!/usr/bin/env python
from __future__ import with_statement
from sandbox import (Sandbox, SandboxConfig,
    SandboxError, Timeout,
    USE_CSANDBOX)
from sys import version_info
import contextlib

class TestException(Exception):
    pass

def createSandboxConfig(*features, **kw):
    if createSandboxConfig.debug:
        features += ("stdout", "stderr")
    return SandboxConfig(*features, **kw)
createSandboxConfig.debug = False

def createSandbox():
    config = createSandboxConfig()
    return Sandbox(config)

def test_valid_code():
    def valid_code():
        assert 1+2 == 3
    createSandbox().call(valid_code)

from os.path import realpath
READ_FILENAME = realpath(__file__)
del realpath

def read_first_line(open):
    with open(READ_FILENAME) as fp:
        line = fp.readline()
    assert line.rstrip() == '#!/usr/bin/env python'

if USE_CSANDBOX:
    def test_open_whitelist():
        from errno import EACCES

        def access_denied():
            try:
                read_first_line(open)
            except IOError, err:
                # Expect a safe_open() error
                assert err.errno == EACCES
                assert err.args[1].startswith('Sandbox deny access to the file ')
            else:
                assert False
        createSandbox().call(access_denied)

        config = createSandboxConfig()
        config.allowPath(READ_FILENAME)
        Sandbox(config).call(read_first_line, open)

        read_first_line(open)

    def test_exec_builtins():
        from sandbox.builtins import ReadOnlyBuiltins

        def check_builtins_type():
            result = []
            exec "result.append(type(__builtins__))" in {'result': result}
            builtin_type = result[0]
            assert builtin_type == ReadOnlyBuiltins
        createSandbox().call(check_builtins_type)
else:
    print "USE_CSANDBOX=False: disable test_open_whitelist(), test_exec_builtins()"

if version_info < (3, 0):
    if USE_CSANDBOX:
        def test_frame_restricted():
            from sys import _getframe

            config = createSandboxConfig(cpython_restricted=True)
            def check_frame_restricted():
                frame = _getframe()
                assert frame.f_restricted == True
            Sandbox(config).call(check_frame_restricted)

            config = createSandboxConfig(cpython_restricted=False)
            def check_frame_not_restricted():
                frame = _getframe()
                assert frame.f_restricted == False
            Sandbox(config).call(check_frame_not_restricted)

            frame = _getframe()
            assert frame.f_restricted == False

        def test_module_frame_restricted():
            from sys import _getframe
            from test_restricted import _test_restricted

            config = createSandboxConfig(cpython_restricted=True)
            def check_module_restricted():
                restricted = _test_restricted(_getframe)
                assert restricted == True
            Sandbox(config).call(check_module_restricted)

            config = createSandboxConfig(cpython_restricted=False)
            def check_module_not_restricted():
                restricted = _test_restricted(_getframe)
                assert restricted == False
            Sandbox(config).call(check_module_not_restricted)
    else:
        print "USE_CSANDBOX=False: disable test_frame_restricted(), test_module_frame_restricted()"

def write_file(filename):
    with open(filename, "w") as fp:
        fp.write("test")

def test_write_file():
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile("wb") as tempfile:
        def write_denied():
            try:
                write_file(tempfile.name)
            except ValueError, err:
                assert str(err) == "Only read modes are allowed."
            else:
                assert False, "writing to a file is not blocked"
        createSandbox().call(write_denied)

    with NamedTemporaryFile("wb") as tempfile:
        write_file(tempfile.name)

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

def test_closure():
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

def test_import():
    def import_blocked():
        try:
            import os
        except ImportError, err:
            assert str(err) == 'Import "os" blocked by the sandbox'
        else:
            assert False
    createSandbox().call(import_blocked)

    # import is allowed outside the sandbox
    import os

def test_import_whitelist():
    # sys.version is allowed by the sandbox
    import sys
    sys_version = sys.version
    del sys

    config = createSandboxConfig()
    config.allowModule('sys', 'version')
    def import_sys():
        import sys
        assert sys.__name__ == 'sys'
        assert sys.version == sys_version
    Sandbox(config).call(import_sys)

def test_readonly_import():
    config = createSandboxConfig()
    config.allowModule('sys', 'version')
    def readonly_module():
        import sys

        try:
            sys.version = '3000'
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False

        try:
            object.__setattr__(sys, 'version', '3000')
        except AttributeError, err:
            assert str(err) == "'SafeModule' object has no attribute 'version'"
        else:
            assert False
    Sandbox(config).call(readonly_module)

def get_file_type_from_stdout():
    import sys
    return type(sys.stdout)

def test_filetype_from_sys_stdout():
    config = createSandboxConfig('stdout')
    def get_file_type_object():
        file_type = get_file_type_from_stdout()
        try:
            read_first_line(file_type)
        except TypeError, err:
            assert str(err) == 'object.__new__() takes no parameters'
        else:
            assert False
    Sandbox(config).call(get_file_type_object)

    file_type = get_file_type_from_stdout()
    read_first_line(file_type)

def get_file_type_from_open_file(filename):
    try:
        with open(filename) as fp:
            return type(fp)
    except SandboxError, err:
        pass

    try:
        with open(filename, 'rb') as fp:
            return type(fp)
    except SandboxError, err:
        pass
    raise TestException("Unable to get file type")

if USE_CSANDBOX:
    def test_filetype_from_open_file():
        filename = READ_FILENAME

        config = createSandboxConfig()
        config.allowPath(filename)
        def get_file_type_object():
            file_type = get_file_type_from_open_file(filename)
            try:
                read_first_line(file_type)
            except TypeError, err:
                assert str(err) == 'object.__new__() takes no parameters'
            else:
                assert False

        Sandbox(config).call(get_file_type_object)

        file_type = get_file_type_from_open_file(filename)
        read_first_line(file_type)
else:
    print "USE_CSANDBOX=False: disable test_filetype_from_open_file()"

def test_exit():
    def exit_noarg():
        try:
            exit()
        except SandboxError, err:
            assert str(err) == "exit() function blocked by the sandbox"
        else:
            assert False
    createSandbox().call(exit_noarg)

    config = createSandboxConfig("exit")
    def exit_1():
        try:
            exit(1)
        except SystemExit, err:
            assert err.args[0] == 1
        else:
            assert False

        import sys
        try:
            sys.exit("bye")
        except SystemExit, err:
            assert err.args[0] == "bye"
        else:
            assert False
    Sandbox(config).call(exit_1)

    try:
        exit(1)
    except SystemExit, err:
        assert err.args[0] == 1
    else:
        assert False

def test_sytem_exit():
    def system_exit_denied():
        try:
            raise SystemExit()
        except NameError, err:
            assert str(err) == "global name 'SystemExit' is not defined"
        except:
            assert False
    createSandbox().call(system_exit_denied)

    config = createSandboxConfig("exit")
    def system_exit_allowed():
        try:
            raise SystemExit()
        except SystemExit:
            pass
        else:
            assert False
    Sandbox(config).call(system_exit_allowed)

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
    def func_globals_denied():
        try:
            get_sandbox_from_func_globals()
        except AttributeError, err:
            assert str(err) == "'function' object has no attribute '__globals__'"
        else:
            assert False
    createSandbox().call(func_globals_denied)

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

# Python 3 doesn't have the builtin file type
if version_info < (3, 0):
    def get_file_type_from_subclasses():
        for subtype in object.__subclasses__():
            if subtype.__name__ == "file":
                return subtype
        raise ValueError("Unable to get file type")

    def test_subclasses():
        def subclasses_denied():
            try:
                get_file_type_from_subclasses()
            except AttributeError, err:
                assert str(err) == "type object 'object' has no attribute '__subclasses__'"
            else:
                assert False
        createSandbox().call(subclasses_denied)

        file_type = get_file_type_from_subclasses()
        read_first_line(file_type)

@contextlib.contextmanager
def capture_stdout():
    import sys
    from StringIO import StringIO

    original = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = original

def test_stdout():
    with capture_stdout() as stdout:
        config = SandboxConfig()
        def print_denied():
            try:
                print "Hello Sandbox 1"
            except SandboxError:
                pass
            else:
                assert False
        Sandbox(config).call(print_denied)

        def print_allowed():
            print "Hello Sandbox 2"
        Sandbox(createSandboxConfig('stdout')).call(print_allowed)

        print "Hello Sandbox 3"

        output = stdout.getvalue()

    assert output == "Hello Sandbox 2\nHello Sandbox 3\n"

def test_read_objectproxy():
    class Person:
        __doc__ = 'Person doc'

        def __str__(self):
            "Convert to string"
            return "str"

        def __repr__(self):
            return "repr"

        def __hash__(self):
            return 42

    person = Person()

    def testPerson(person):
        assert person.__doc__ == 'Person doc'

        assert person.__str__() == "str"
        assert person.__repr__() == "repr"
        assert person.__hash__() == 42

        assert person.__str__.__name__ == "__str__"
        assert person.__str__.__doc__ == "Convert to string"

    testPerson(person)

    sandbox = createSandbox()
    sandbox.call(testPerson, person)

if USE_CSANDBOX:
    def test_modify_objectproxy():
        class Person:
            def __init__(self, name):
                self.name = name

        # Attribute
        def setAttr(person):
            person.name = "victor"

        person = Person("haypo")
        sandbox = createSandbox()
        try:
            sandbox.call(setAttr, person)
        except SandboxError, err:
            assert str(err) == 'Read only object'
        else:
            assert False

        setAttr(person)
        assert person.name == "victor"

        # Delete attribute
        def delAttr(person):
            del person.name

        person = Person("haypo")
        sandbox = createSandbox()
        try:
            sandbox.call(delAttr, person)
        except SandboxError, err:
            assert str(err) == 'Read only object'
        else:
            assert False

        delAttr(person)
        assert hasattr(person, 'name') == False

        # Dictionary
        def setDict(person):
            person.__dict__['name'] = "victor"

        person = Person("haypo")
        try:
            sandbox.call(setDict, person)
        except SandboxError, err:
            assert str(err) == 'Read only object'
        else:
            assert False

        setDict(person)
        assert person.name == "victor"
else:
    print "USE_CSANDBOX=False: disable test_modify_objectproxy()"

def builtins_superglobal():
    if isinstance(__builtins__, dict):
        __builtins__['SUPERGLOBAL'] = 42
        assert SUPERGLOBAL == 42
        del __builtins__['SUPERGLOBAL']
    else:
        __builtins__.SUPERGLOBAL = 42
        assert SUPERGLOBAL == 42
        del __builtins__.SUPERGLOBAL

def test_modify_builtins():
    def readonly_builtins():
        try:
            builtins_superglobal()
        except SandboxError, err:
            assert str(err) == "Read only object"
        else:
            assert False
    createSandbox().call(readonly_builtins)

    builtins_superglobal()

def builtins_dict_superglobal():
    dict.__setitem__(__builtins__, 'SUPERGLOBAL', 42)
    assert SUPERGLOBAL == 42
    del __builtins__['SUPERGLOBAL']

def test_modify_builtins_dict():
    def readonly_builtins_dict():
        try:
            builtins_dict_superglobal()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__setitem__'"
        else:
            assert False
    createSandbox().call(readonly_builtins_dict)

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

def test_del_builtin():
    def del_builtin_denied():
        try:
            del_builtin_import()
        except AttributeError, err:
            assert str(err) == "type object 'dict' has no attribute '__delitem__'"
        else:
            assert False

    config = createSandboxConfig()
    config.allowModule('sys')
    Sandbox(config).call(del_builtin_denied)

def test_timeout():
    def denial_of_service():
        try:
            while 1:
                pass
        except Timeout:
            pass

    config = createSandboxConfig()
    config.timeout = 0.1
    Sandbox(config).call(denial_of_service)

def test_execute():
    code = "assert globals().keys() == locals().keys() == ['__builtins__']"
    createSandbox().execute(code)

    code = "assert globals().keys() == locals().keys() == ['a']"
    createSandbox().execute(code, globals={'a': 0})

def replace_func_code():
    def add(x, y):
        return x + y
    def substract(x, y):
        return x - y
    try:
        add.func_code = substract.func_code
    except AttributeError:
        add.__code__ = substract.__code__
    return add(52, 10)

def test_func_code():
    try:
        createSandbox().call(replace_func_code)
    except AttributeError, err:
        assert str(err) == "'function' object has no attribute '__code__'"
    else:
        assert False

    assert replace_func_code() == 42

def execfile_test(filename):
    execfile(filename)

def test_execfile():
    from tempfile import NamedTemporaryFile
    from StringIO import StringIO

    with NamedTemporaryFile() as script:
        print >>script, "print('Hello World!')"
        script.flush()

        filename = script.name

        config = createSandboxConfig('stdout')
        try:
            Sandbox(config).call(execfile_test, filename)
        except NameError, err:
            assert str(err) == "global name 'execfile' is not defined"
        else:
            assert False

        with capture_stdout() as stdout:
            execfile_test(filename)
            output = stdout.getvalue()
            print(repr(output))
            assert output.startswith('Hello World')

def get_code_args():
    def somme(a, b):
        return a+b
    fcode = somme.func_code
    # code constructor arguments
    return (
        fcode.co_argcount,
        fcode.co_nlocals,
        fcode.co_stacksize,
        fcode.co_flags,
        fcode.co_code,
        fcode.co_consts,
        fcode.co_names,
        fcode.co_varnames,
        fcode.co_filename,
        fcode.co_name,
        fcode.co_firstlineno,
        fcode.co_lnotab,
    )

def code_objects():
    try:
        yield compile("1", "<string>", "eval")
    except NameError:
        pass

    # Function code
    def func():
        pass
    try:
        yield func.__code__
    except AttributeError:
        pass

    # Generator code
    def generator():
        yield
    gen = generator()
    try:
        yield gen.gi_code
    except AttributeError:
        pass

    # Frame code
    import sys
    frame = sys._getframe(0)
    try:
        yield frame.f_code
    except AttributeError:
        pass

def create_code_objects(args):
    for code_obj in code_objects():
        code_type = type(code_obj)
        try:
            return code_type(*args)
        except SandboxError, err:
            assert str(err) == 'code() blocked by the sandbox'
    raise TestException("Unable to get code type")

def exec_bytecode(code_args):
    def func():
        pass
    function_type = type(func)
    fcode = create_code_objects(code_args)
    new_func = function_type(fcode, {}, "new_func")
    return new_func(1, 2)

if USE_CSANDBOX:
    def test_bytecode():
        code_args = get_code_args()

        config = createSandboxConfig('code')
        config.allowModule('sys', '_getframe')
        try:
            Sandbox(config).call(exec_bytecode, code_args)
        except TestException, err:
            assert str(err) == "Unable to get code type"
        else:
            assert False

        assert exec_bytecode(code_args) == 3
else:
    print "USE_CSANDBOX=False: disable test_bytecode()"

def get_file_type_from_stdout_method():
    import sys
    return type(sys.stdout.__enter__())

def test_method_proxy():
    config = createSandboxConfig('stdout')
    def get_file_type_object():
        file_type = get_file_type_from_stdout_method()
        try:
            read_first_line(file_type)
        except TypeError, err:
            assert str(err) == 'object.__new__() takes no parameters'
        else:
            assert False
    Sandbox(config).call(get_file_type_object)

    file_type = get_file_type_from_stdout_method()
    read_first_line(file_type)

def test_compile():
    import sys

    orig_displayhook = sys.displayhook
    try:
        results = []
        def displayhook(value):
            results.append(value)

        sys.displayhook = displayhook

        def _test_compile():
            exec compile("1+1", "<string>", "single") in {}
            assert results == [2]
        config = createSandboxConfig('code')
        Sandbox(config).call(_test_compile)

        del results[:]
        _test_compile()
    finally:
        sys.displayhook = orig_displayhook

def check_frame_filename():
    import sys
    frame = sys._getframe(1)
    fcode = frame.f_code
    assert fcode.co_filename == __file__

def test_traceback():
    config = createSandboxConfig('traceback')
    config.allowModule('sys', '_getframe')
    Sandbox(config).call(check_frame_filename)

    check_frame_filename()

def parseOptions():
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [options]")
    parser.add_option("--raise",
        help="Don't catch exception",
        dest="raise_exception",
        action="store_true")
    parser.add_option("--debug",
        help="Enable debug mode (enable stdout and stderr features)",
        action="store_true")
    options, argv = parser.parse_args()
    if argv:
        parser.print_help()
        exit(1)
    return options

def main():
    global createSandboxConfig

    options = parseOptions()

    createSandboxConfig.debug = options.debug

    # Get all tests
    all_tests = []
    _locals = globals().items()
    for name, value in _locals:
        if not name.startswith("test"):
            continue
        all_tests.append(value)
    all_tests.sort(key=lambda func: func.__name__)

    # Run tests
    nerror = 0
    for func in all_tests:
        name = func.__name__
        try:
            func()
        except BaseException, err:
            nerror += 1
            print "Test %s: FAILED! %r" % (name, err)
            if options.raise_exception:
                raise
        else:
            print "Test %s: ok" % name

    # Exit
    from sys import exit
    print
    if nerror:
        print "%s ERRORS!" % nerror
        exit(1)
    else:
        print "%s tests succeed" % len(all_tests)
        exit(0)

if __name__ == "__main__":
    main()

