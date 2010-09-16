from __future__ import with_statement
from sandbox import Sandbox, SandboxError, USE_CSANDBOX
from sandbox.test import (createSandbox, createSandboxConfig,
    SkipTest, TestException)
from sandbox.test.tools import read_first_line, READ_FILENAME
from sys import version_info

def _get_file_type(obj):
    if version_info >= (3, 0):
        if hasattr(obj, "buffer"):
            # TextIOWrapper => BufferedXXX
            obj = obj.buffer
        if hasattr(obj, "raw"):
            # BufferedXXX => _FileIO
            obj = obj.raw
    return type(obj)

def test_open_whitelist():
    if not USE_CSANDBOX:
        raise SkipTest("require _sandbox")

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

def test_write_file():
    def write_file(filename):
        with open(filename, "w") as fp:
            fp.write("test")

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

def test_filetype_from_sys_stdout():
    def get_file_type_from_stdout():
        import sys
        return _get_file_type(sys.stdout)

    config = createSandboxConfig('stdout')
    def get_file_type_object():
        file_type = get_file_type_from_stdout()
        try:
            read_first_line(file_type)
        except TypeError, err:
            assert str(err) in ('object.__new__() takes no parameters', 'default __new__ takes no parameters')
        else:
            assert False
    Sandbox(config).call(get_file_type_object)

    file_type = get_file_type_from_stdout()
    read_first_line(file_type)

def test_filetype_from_open_file():
    if not USE_CSANDBOX:
        raise SkipTest("require _sandbox")

    def get_file_type_from_open_file(filename):
        try:
            with open(filename) as fp:
                return _get_file_type(fp)
        except SandboxError:
            pass

        try:
            with open(filename, 'rb') as fp:
                return type(fp)
        except SandboxError:
            pass
        raise TestException("Unable to get file type")

    filename = READ_FILENAME

    config = createSandboxConfig()
    config.allowPath(filename)
    def get_file_type_object():
        file_type = get_file_type_from_open_file(filename)
        try:
            read_first_line(file_type)
        except TypeError, err:
            assert str(err) in ('object.__new__() takes no parameters', 'default __new__ takes no parameters')
        else:
            assert False

    Sandbox(config).call(get_file_type_object)

    file_type = get_file_type_from_open_file(filename)
    read_first_line(file_type)

def test_method_proxy():
    def get_file_type_from_stdout_method():
        import sys
        return _get_file_type(sys.stdout.__enter__())

    config = createSandboxConfig('stdout')
    def get_file_type_object():
        file_type = get_file_type_from_stdout_method()
        try:
            read_first_line(file_type)
        except TypeError, err:
            assert str(err) in ('object.__new__() takes no parameters', 'default __new__ takes no parameters')
        else:
            assert False
    Sandbox(config).call(get_file_type_object)

    file_type = get_file_type_from_stdout_method()
    read_first_line(file_type)

def test_subclasses():
    if version_info >= (3, 0):
        raise SkipTest("Python 3 has not file type")

    def get_file_type_from_subclasses():
        for subtype in object.__subclasses__():
            if subtype.__name__ == "file":
                return subtype
        raise ValueError("Unable to get file type")

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

