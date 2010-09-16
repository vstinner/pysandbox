from subprocess import Popen, PIPE, STDOUT
from sandbox.test.tools import bytes_literal
import os
import sys

def get_interpreter_stdout(*code, **kw):
    encoding = kw.get('encoding', 'utf-8')

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = encoding
    process = Popen(
        [sys.executable, 'interpreter.py', '-q'],
        stdin=PIPE, stdout=PIPE, stderr=STDOUT,
        env=env)
    code += (u'exit()',)
    code = '\n'.join(code)
    code = code.encode(encoding)
    stdout, stderr = process.communicate(code)
    if process.returncode != 0:
        raise AssertionError(
            "Process error: exit code=%s, stdout=%r"
            % (process.returncode, stdout))
    assert process.returncode == 0
    stdout = stdout.splitlines()
    assert stdout[0] == bytes_literal(''), stdout[0]
    assert stdout[1] == bytes_literal(''), stdout[1]
    return stdout[2:]

def test_interpreter():
    stdout = get_interpreter_stdout('1+1')
    assert stdout == [bytes_literal(r"sandbox>>> 2"), bytes_literal('sandbox>>> ')]

    for encoding in ('latin_1', 'utf_8'):
        stdout = get_interpreter_stdout(u'u"\xe9"', encoding=encoding)
        assert stdout == [bytes_literal(r"sandbox>>> u'\xe9'"), bytes_literal('sandbox>>> ')]

