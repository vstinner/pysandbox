from __future__ import with_statement, absolute_import
from sandbox import SandboxError, Timeout
from sandbox.subprocess_child import call_child
import os
import pickle
import subprocess
import sys
import tempfile
import time
try:
    import fcntl
except ImportError:
    set_cloexec_flag = None
else:
    def set_cloexec_flag(fd):
        try:
            cloexec_flag = fcntl.FD_CLOEXEC
        except AttributeError:
            cloexec_flag = 1
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags | cloexec_flag)
try:
    from time import monotonic as monotonic_time
except ImportError:
    # Python < 3.3
    from time import time as monotonic_time

def wait_child(config, pid, sigkill):
    if config.timeout:
        timeout = monotonic_time() + config.timeout
        kill = False
        status = os.waitpid(pid, os.WNOHANG)
        while status[0] == 0:
            dt = timeout - monotonic_time()
            if dt < 0:
                os.kill(pid, sigkill)
                status = os.waitpid(pid, 0)
                raise Timeout()

            if dt > 1.0:
                pause = 0.100
            else:
                pause = 0.010
            # TODO: handle SIGCHLD to avoid wasting time in polling
            time.sleep(pause)
            status = os.waitpid(pid, os.WNOHANG)
    else:
        status = os.waitpid(pid, 0)
    if status[0] != pid:
        raise Exception("got the status of the wrong process!")
    return status[1]

def call_parent(config, pid, rpipe):
    import signal
    sigkill = signal.SIGKILL
    try:
        status = wait_child(config, pid, sigkill)
    except:
        os.close(rpipe)
        raise
    if status != 0:
        if os.WIFSIGNALED(status):
            signum = os.WTERMSIG(status)
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
    if set_cloexec_flag is not None:
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
        return call_parent(sandbox.config, pid, rpipe)

def execute_subprocess(sandbox, code, globals, locals):
    config = sandbox.config
    input_filename = tempfile.mktemp()
    output_filename = tempfile.mktemp()
    args = (
        sys.executable,
        # FIXME: use '-S'
        '-E',
        '-m', 'sandbox.subprocess_child',
        input_filename, output_filename,
    )

    input_data = {
        'code': code,
        'config': config,
        'locals': locals,
        'globals': globals,
    }

    try:
        # serialize input data
        with open(input_filename, 'wb') as input_file:
            pickle.dump(input_data, input_file)
            if config.max_input_size:
                size = input_file.tell()
                if size > config.max_input_size:
                    raise SandboxError("Input data are too big: %s bytes (max=%s)"
                                       % (size, config.max_input_size))

        # create the subprocess
        process = subprocess.Popen(args, close_fds=True, shell=False)

        # wait process exit
        if config.timeout:
            timeout = monotonic_time() + config.timeout
            kill = False
            exitcode = process.poll()
            while exitcode is None:
                dt = timeout - monotonic_time()
                if dt < 0:
                    process.terminate()
                    exitcode = process.wait()
                    raise Timeout()

                if dt > 1.0:
                    pause = 0.5
                else:
                    pause = 0.1
                # TODO: handle SIGCHLD to avoid wasting time in polling
                time.sleep(pause)
                exitcode = process.poll()
        else:
            exitcode = process.wait()
        os.unlink(input_filename)
        input_filename = None

        # handle child process error
        if exitcode:
            if os.name != "nt" and exitcode < 0:
                signum = -exitcode
                text = "subprocess killed by signal %s" % signum
            else:
                text = "subprocess failed with exit code %s" % exitcode
            raise SandboxError(text)

        with open(output_filename, 'rb') as output_file:
            if config.max_output_size:
                output_file.seek(0, 2)
                size = output_file.tell()
                output_file.seek(0)
                if size > config.max_output_size:
                    raise SandboxError("Output data are too big: %s bytes (max=%s)"
                                       % (size, config.max_output_size))
            output_data = pickle.load(output_file)
        os.unlink(output_filename)
        output_filename = None
    finally:
        temp_filenames = []
        if input_filename is not None:
            temp_filenames.append(input_filename)
        if output_filename is not None:
            temp_filenames.append(output_filename)
        for filename in temp_filenames:
            try:
                os.unlink(filename)
            except OSError:
                pass

    if 'error' in output_data:
        raise output_data['error']
    if locals is not None:
        locals.clear()
        locals.update(output_data['locals'])
    if globals is not None:
        globals.clear()
        globals.update(output_data['globals'])
    return output_data['result']

