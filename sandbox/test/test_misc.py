from __future__ import with_statement
from sandbox import Sandbox, SandboxError, SandboxConfig
from sandbox.test import createSandbox, createSandboxConfig
from sandbox.test.tools import capture_stdout

def test_valid_code():
    def valid_code():
        assert 1+2 == 3
    createSandbox().call(valid_code)

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

def test_traceback():
    def check_frame_filename():
        import sys
        frame = sys._getframe(1)
        frame_code = frame.f_code
        frame_filename = frame_code.co_filename
        # it may ends with .py or .pyc
        assert __file__.startswith(frame_filename)

    config = createSandboxConfig('traceback')
    config.allowModule('sys', '_getframe')
    Sandbox(config).call(check_frame_filename)

    check_frame_filename()

def test_regex():
    def check_regex():
        import re
        assert re.escape('+') == '\\+'
        assert re.match('a+', 'aaaa').group(0) == 'aaaa'
        # FIXME: Remove this workaround: list(...)
        assert list(re.findall('.', 'abc')) == ['a', 'b', 'c']
        assert re.search('a+', 'aaaa').group(0) == 'aaaa'
        # FIXME: Remove this workaround: list(...)
        assert list(re.split(' +', 'a b    c')) == ['a', 'b', 'c']
        assert re.sub('a+', '#', 'a b aa c') == '# b # c'

    sandbox = createSandbox('regex')
    sandbox.call(check_regex)

    check_regex()


