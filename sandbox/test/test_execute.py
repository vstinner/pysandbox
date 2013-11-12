from __future__ import with_statement
from sys import version_info
from sandbox import Sandbox, HAVE_PYPY
from sandbox.test import createSandbox, createSandboxConfig, SkipTest
from sandbox.test.tools import capture_stdout

def test_execute():
    def test(*lines, **kw):
        code = "; ".join(lines)
        config = createSandboxConfig()
        if HAVE_PYPY:
            # FIXME: is it really needed?
            config._builtins_whitelist.add('compile')
        Sandbox(config).execute(code, **kw)

    test(
        "assert globals() is locals(), 'test_execute #1a'",
        "assert list(globals().keys()) == list(locals().keys()) == ['__builtins__'], 'test_execute #1b'",
        "x=42")

    namespace = {'a': 1}
    test(
        "assert globals() is locals(), 'test_execute #2a'",
        "assert list(globals().keys()) == list(locals().keys()) == ['a', '__builtins__'], 'test_execute #2b'",
        "a=10",
        "x=42",
        globals=namespace)
    assert set(namespace.keys()) == set(('a', 'x', '__builtins__'))
    assert namespace['a'] == 10
    assert namespace['x'] == 42

    namespace = {'b': 2}
    test(
        "assert globals() is not locals(), 'test_execute #3a'",
        "assert list(globals().keys()) == ['__builtins__'], 'test_execute #3b'",
        "assert list(locals().keys()) == ['b'], 'test_execute #3c'",
        "b=20",
        "x=42",
        locals=namespace)
    assert namespace == {'b': 20, 'x': 42}

    my_globals = {'a': 1}
    namespace = {'b': 2}
    test(
        "assert globals() is not locals(), 'test_execute #4a'",
        "assert list(globals().keys()) == ['a', '__builtins__'], 'test_execute #4b'",
        "assert list(locals().keys()) == ['b'], 'test_execute #4c'",
        "x=42",
        "a=10",
        "b=20",
        globals=my_globals,
        locals=namespace)
    assert set(my_globals.keys()) == set(('a', '__builtins__'))
    assert my_globals['a'] == 1
    assert namespace == {'a': 10, 'b': 20, 'x': 42}

    namespace = {}
    test('a=1', locals=namespace)
    assert namespace == {'a': 1}, namespace

def test_execfile():
    if version_info >= (3, 0):
        raise SkipTest("execfile() only exists in Python 2.x")

    def execfile_test(filename):
        execfile(filename)

    from tempfile import NamedTemporaryFile

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

