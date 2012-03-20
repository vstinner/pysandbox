from __future__ import absolute_import
from cStringIO import StringIO
from sandbox import SandboxError, Timeout
import fcntl
import os
import pickle
import subprocess
import sys
from signal import SIGALRM

def apply_limits(config):
    try:
        import resource
    except ImportError:
        resource = None
    else:
        # deny fork and thread
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

    if config.max_memory:
        if not resource:
            raise NotImplementedError("SubprocessConfig.max_memory is not implemented for your platform")
        resource.setrlimit(resource.RLIMIT_AS, (config.max_memory, config.max_memory))

    if config.timeout:
        import math, signal
        seconds = int(math.ceil(config.timeout))
        seconds = max(seconds, 1)
        signal.alarm(seconds)

def encode_error(err):
    return pickle.dumps(err)
    return (type(err).__name__, str(err))

def raise_error(data):
    err = pickle.loads(data)
    raise err

    err_type, err_msg = data
    raise Exception('[%s] %s' % (err_type, err_msg))

def child_process():
    from sandbox import Sandbox

    output = sys.stdout
    redirect_stdout = False #True
    if redirect_stdout:
        sys.stdout = StringIO()
        sys.stderr = sys.stdout
    try:
        input_data = pickle.load(sys.stdin)
        config = input_data['config']
        apply_limits(config)

        sandbox = Sandbox(config)
        code = input_data['code']
        locals = input_data.get('locals')
        globals = input_data.get('globals')
        result = sandbox._execute(code, globals, locals)
        output_data = {'result': result}
        if 'globals' in input_data:
            del globals['__builtins__']
            output_data['globals'] = globals
        if 'locals' in input_data:
            output_data['locals'] = locals
    except BaseException, err:
        output_data = {'error': encode_error(err)}
    if redirect_stdout:
        output_data['stdout'] = sys.stdout.getvalue()
    pickle.dump(output_data, output)

def child_call(wpipe, sandbox, func, args, kw):
    try:
        result = sandbox._call(func, args, kw)
        data = {'result': result}
    except BaseException, err:
        data = {'error': encode_error(err)}
    output = os.fdopen(wpipe, 'wb')
    pickle.dump(data, output)
    output.flush()
    output.close()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

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
            os._exit(0)
    else:
        os.close(wpipe)
        try:
            status = os.waitpid(pid, 0)[1]
        except:
            os.close(rpipe)
            raise
        rpipe_file = os.fdopen(rpipe, 'rb')
        try:
            data = pickle.load(rpipe_file)
        finally:
            rpipe_file.close()
        if 'error' in data:
            raise_error(data['error'])
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
    args = (sys.executable, '-E', '-S', '-m', __name__)
    kw = {
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.STDOUT,
        'close_fds': True,
        'shell': False,
    }

    # create the subprocess
    process = subprocess.Popen(args, **kw)

    # wait data
    stdout, stderr = process.communicate(pickle.dumps(input_data))
    exitcode = process.wait()
    if exitcode:
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

    output_data = pickle.loads(stdout)
    if 'stdout' in output_data:
        sys.stdout.write(output_data['stdout'])
        sys.stdout.flush()
    if 'error' in output_data:
        raise_error(output_data['error'])
    if 'locals' in input_data:
        input_data['locals'].clear()
        input_data['locals'].update(output_data['locals'])
    if 'globals' in input_data:
        input_data['globals'].clear()
        input_data['globals'].update(output_data['globals'])
    return output_data['result']

if __name__ == "__main__":
    child_process()

