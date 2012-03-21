from __future__ import absolute_import
from sandbox import SandboxError, Timeout
import fcntl
import os
import pickle
import subprocess
import sys
from signal import SIGALRM
from sandbox.subprocess_child import child_call, USE_STDIN_PIPE, USE_STDOUT_PIPE
if not USE_STDOUT_PIPE:
    import tempfile

def set_cloexec_flag(fd):
    try:
        cloexec_flag = fcntl.FD_CLOEXEC
    except AttributeError:
        cloexec_flag = 1
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags | cloexec_flag)

def call_fork(sandbox, func, args, kw):
    rpipe, wpipe = os.pipe()
    set_cloexec_flag(wpipe)
    pid = os.fork()
    if pid == 0:
        os.close(rpipe)
        try:
            child_call(wpipe, sandbox, func, args, kw)
        finally:
            # FIXME: handle error differently?
            os._exit(1)
    else:
        os.close(wpipe)
        try:
            status = os.waitpid(pid, 0)[1]
        except:
            os.close(rpipe)
            raise
        if status != 0:
            if os.WIFSIGNALED(status):
                signum = os.WTERMSIG(status)
                if signum == SIGALRM:
                    raise Timeout()
                text = "subprocess killed by signal %s" % signum
            elif os.WIFEXITED(status):
                exitcode = os.WEXITSTATUS(status)
                text = "subprocess failed with exit code %s" % exitcode
            else:
                text = "subprocess failed"
            raise SandboxError(text)
        rpipe_file = os.fdopen(rpipe, 'rb')
        try:
            data = pickle.load(rpipe_file)
        finally:
            rpipe_file.close()
        if 'error' in data:
            raise data['error']
        return data['result']

def execute_subprocess(sandbox, code, globals, locals):
    # prepare data
    input_data = {
        'code': code,
        'config': sandbox.config,
    }
    if locals is not None:
        input_data['locals'] = locals
    if globals is not None:
        input_data['globals'] = globals

    # FIXME: use '-S'
    args = (sys.executable, '-E', '-m', 'sandbox.subprocess_child')
    kw = {
        'close_fds': True,
        'shell': False,
    }
    if USE_STDIN_PIPE:
        kw['stdin'] = subprocess.PIPE
    else:
        args += (pickle.dumps(input_data),)
    if USE_STDOUT_PIPE:
        kw['stdout'] = subprocess.PIPE
    else:
        output_file = tempfile.NamedTemporaryFile()
        args += (output_file.name,)

    try:
        # create the subprocess
        process = subprocess.Popen(args, **kw)

        # wait data
        if USE_STDOUT_PIPE:
            if USE_STDIN_PIPE:
                stdout, stderr = process.communicate(pickle.dumps(input_data))
            else:
                stdout, stderr = process.communicate()
        else:
            if USE_STDIN_PIPE:
                pickle.dump(process.stdin)
                process.stdin.flush()
        exitcode = process.wait()
        if exitcode:
            if USE_STDOUT_PIPE:
                sys.stdout.write(stdout)
                sys.stdout.flush()

            if os.name != "nt" and exitcode < 0:
                signum = -exitcode
                if signum == SIGALRM:
                    raise Timeout()
                text = "subprocess killed by signal %s" % signum
            else:
                text = "subprocess failed with exit code %s" % exitcode
            raise SandboxError(text)

        if USE_STDOUT_PIPE:
            output_data = pickle.loads(stdout)
        else:
            output_data = pickle.load(output_file)
    finally:
        if not USE_STDOUT_PIPE:
            output_file.close()

    if 'stdout' in output_data:
        sys.stdout.write(output_data['stdout'])
        sys.stdout.flush()
    if 'error' in output_data:
        raise output_data['error']
    if 'locals' in input_data:
        input_data['locals'].clear()
        input_data['locals'].update(output_data['locals'])
    if 'globals' in input_data:
        input_data['globals'].clear()
        input_data['globals'].update(output_data['globals'])
    return output_data['result']

