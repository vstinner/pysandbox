from __future__ import with_statement
from os.path import join as path_join, basename, realpath
from glob import glob
from sys import version_info
import contextlib

READ_FILENAME = realpath(__file__)
FIRST_LINE = open(READ_FILENAME, 'rb').readline()

if version_info >= (3, 0):
    # function for python2/python3 compatibility: bytes literal string
    def bytes_literal(text):
        return text.encode('ascii')
else:
    def bytes_literal(text):
        return text

def _getTests(module_dict, all_tests, keyword):
    _locals = module_dict.items()
    for name, value in _locals:
        if not name.startswith("test"):
            continue
        if keyword and (keyword not in name[4:]):
            continue
        all_tests.append(value)

def getTests(main_dict, keyword=None):
    all_tests = []
    _getTests(main_dict, all_tests, keyword)
    for filename in glob(path_join("sandbox", "test", "test_*.py")):
        # sandbox/test/test_bla.py => sandbox.test.bla
        module_name = basename(filename)[:-3]
        full_module_name = "sandbox.test.%s" % module_name
        parent_module = __import__(full_module_name)
        module = getattr(parent_module.test, module_name)
        _getTests(module.__dict__, all_tests, keyword)
    all_tests.sort(key=lambda func: func.__name__)
    return all_tests

def read_first_line(open):
    with open(READ_FILENAME, 'rb') as fp:
        line = fp.readline()
    assert line == FIRST_LINE

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

