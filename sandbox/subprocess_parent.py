from __future__ import with_statement, absolute_import
from sandbox import SandboxError, Timeout
from sandbox.subprocess_child import call_child
from signal import SIGALRM
import fcntl
import os
import pickle
import subprocess
import sys
import tempfile

def set_cloexec_flag(fd):
    try:
        cloexec_flag = fcntl.FD_CLOEXEC
    except AttributeError:
        cloexec_flag = 1
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags | cloexec_flag)

def call_parent(pid, rpipe):
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

def call_fork(sandbox, func, args, kw):
    rpipe, wpipe = os.pipe()
    set_cloexec_flag(wpipe)
    pid = os.fork()
    if pid == 0:
        os.close(rpipe)
        try:
            call_child(wpipe, sandbox, func, args, kw)
        finally:
            # FIXME: handle error differently?
            os._exit(1)
    else:
        os.close(wpipe)
        return call_parent(pid, rpipe)

def execute_subprocess(sandbox, code, globals, locals):
    old_umask = os.umask(0177)
    try:
        input_file = tempfile.NamedTemporaryFile()
        output_file = tempfile.NamedTemporaryFile()
    finally:
        os.umask(old_umask)

    try:
        input_data = {
            'code': code,
            'config': sandbox.config,
            'locals': locals,
            'globals': globals,
        }
        args = (
            sys.executable,
            # FIXME: use '-S'
            '-E',
            '-m', 'sandbox.subprocess_child',
            input_file.name, output_file.name)
        pickle.dump(input_data, input_file)
        input_file.flush()
        if sandbox.config.max_input_size:
            size = input_file.tell()
            if size > sandbox.config.max_input_size:
                raise SandboxError("Input data are too big: %s bytes (max=%s)"
                                   % (size, sandbox.config.max_input_size))

        # create the subprocess
        process = subprocess.Popen(args, close_fds=True, shell=False)

        # wait data
        exitcode = process.wait()
        if exitcode:
            if os.name != "nt" and exitcode < 0:
                signum = -exitcode
                if signum == SIGALRM:
                    raise Timeout()
                text = "subprocess killed by signal %s" % signum
            else:
                text = "subprocess failed with exit code %s" % exitcode
            raise SandboxError(text)

        if sandbox.config.max_output_size:
            output_file.seek(0, 2)
            size = output_file.tell()
            output_file.seek(0)
            if size > sandbox.config.max_output_size:
                raise SandboxError("Output data are too big: %s bytes (max=%s)"
                                   % (size, sandbox.config.max_output_size))
        output_data = pickle.load(output_file)
    finally:
        input_file.close()
        output_file.close()

    if 'error' in output_data:
        raise output_data['error']
    if locals is not None:
        locals.clear()
        locals.update(output_data['locals'])
    if globals is not None:
        globals.clear()
        globals.update(output_data['globals'])
    return output_data['result']

