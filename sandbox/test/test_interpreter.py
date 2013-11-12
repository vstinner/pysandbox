from subprocess import Popen, PIPE
from sandbox.test.tools import bytes_literal
import os
import sys
from sys import version_info
from locale import getpreferredencoding

def check_interpreter_stdout(code, expected, **kw):
    encoding = kw.get('encoding', 'utf-8')

    env = os.environ.copy()
    # Use dummy terminal type to avoid 8 bits mode
    # escape sequence ('\x1b[?1034h')
    env['TERM'] = 'dumb'
    env['PYTHONIOENCODING'] = encoding
    process = Popen(
        [sys.executable, 'interpreter.py', '-q'],
        stdin=PIPE, stdout=PIPE, stderr=PIPE,
        env=env)
    code += u'\nexit()'
    code = code.encode(encoding)
    stdout, stderr = process.communicate(code)
    if process.returncode != 0:
        raise AssertionError(
            "Process error: exit code=%s, stdout=%r"
            % (process.returncode, stdout))
    assert process.returncode == 0
    stdout = stdout.splitlines()
    assert stdout[0] == bytes_literal(''), stdout[0]
    stdout = stdout[1:]
    assert stdout == expected, "%s != %s" % (stdout, expected)

# FIXME: interpreter feature was broken in pysandbox 1.5.1 since the builtin
# compile() function is now blocked
def XXXtest_interpreter():
    check_interpreter_stdout('1+1',
        [bytes_literal(r"sandbox>>> 2"),
         bytes_literal('sandbox>>> ')])

    if version_info >= (3, 0):
        code = u'print(ascii("\xe9"))'
        expected = u"'\\xe9'"
    else:
        code = u'print(repr(u"\xe9"))'
        expected = u"u'\\xe9'"
    for encoding in ('latin_1', 'utf_8'):
        check_interpreter_stdout(code,
            [bytes_literal(r"sandbox>>> " + expected),
             bytes_literal(''),
             bytes_literal('sandbox>>> ')],
            encoding=encoding)

