import sys
import os
import pickle
from sandbox import Sandbox

USE_STDIN_PIPE = False
USE_STDOUT_PIPE = False
if USE_STDOUT_PIPE:
    from cStringIO import StringIO

try:
    import resource
except ImportError:
    resource = None

def enable_process_limits(config):
    if resource is not None:
        # deny fork and thread
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

    if not config.has_feature("stdin"):
        stdin_fd = sys.__stdin__.fileno()
        devnull = os.open(os.devnull, os.O_RDONLY)
        os.dup2(devnull, stdin_fd)

    if not config.has_feature("stdout") \
    or not config.has_feature("stderr"):
        devnull = os.open(os.devnull, os.O_WRONLY)
        if not USE_STDOUT_PIPE \
        and not config.has_feature("stdout"):
            stdout_fd = sys.__stdout__.fileno()
            os.dup2(devnull, stdout_fd)
        if not config.has_feature("stderr"):
            stderr_fd = sys.__stderr__.fileno()
            os.dup2(devnull, stderr_fd)

    if config.max_memory:
        if not resource:
            raise NotImplementedError("SandboxConfig.max_memory is not implemented on your platform")
        resource.setrlimit(resource.RLIMIT_AS, (config.max_memory, -1))

    if config.timeout:
        import math, signal
        seconds = int(math.ceil(config.timeout))
        seconds = max(seconds, 1)
        signal.alarm(seconds)

def execute_child():
    if USE_STDOUT_PIPE:
        output = sys.stdout
        sys.stdout = StringIO()
    else:
        if USE_STDIN_PIPE:
            output_filename = sys.argv[1]
        else:
            output_filename = sys.argv[2]
        output = open(output_filename, "wb")
    base_exception = BaseException
    try:
        if USE_STDIN_PIPE:
            input_data = pickle.load(sys.stdin)
        else:
            input_data = sys.argv[1]
            input_data = pickle.loads(input_data)
        config = input_data['config']
        enable_process_limits(config)

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
    except base_exception, err:
        output_data = {'error': err}
    if USE_STDOUT_PIPE:
        output_data['stdout'] = sys.stdout.getvalue()
    pickle.dump(output_data, output)
    output.flush()
    if not USE_STDOUT_PIPE:
        output.close()

def child_call(wpipe, sandbox, func, args, kw):
    config = sandbox.config
    try:
        enable_process_limits(config)
        result = sandbox._call(func, args, kw)
        data = {'result': result}
    except BaseException, err:
        data = {'error': err}
    output = os.fdopen(wpipe, 'wb')
    pickle.dump(data, output)
    output.flush()
    output.close()
    if config.has_feature("stdout"):
        sys.stdout.flush()
    if config.has_feature("stderr"):
        sys.stderr.flush()
    os._exit(0)

if __name__ == "__main__":
    execute_child()

