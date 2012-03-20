import sys
import os
import pickle
from sandbox import Sandbox
#from cStringIO import StringIO

try:
    import resource
except ImportError:
    resource = None

class ProcessLimits:
    def __init__(self, config):
        self.config = config
        self.old_max_memory = None

    def enable(self):
        if resource is not None:
            # deny fork and thread
            resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

        if self.config.max_memory:
            if not resource:
                raise NotImplementedError("SubprocessConfig.max_memory is not implemented for your platform")
            self.old_max_memory = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (self.config.max_memory, -1))

        if self.config.timeout:
            import math, signal
            seconds = int(math.ceil(self.config.timeout))
            seconds = max(seconds, 1)
            signal.alarm(seconds)

    def disable(self):
        if self.old_max_memory is not None:
            resource.setrlimit(resource.RLIMIT_AS, self.old_max_memory)

def execute_child():
    output = sys.stdout
    # FIXME: don't use stdout
    redirect_stdout = False #True
    if redirect_stdout:
        sys.stdout = StringIO()
        sys.stderr = sys.stdout
    try:
        input_data = pickle.load(sys.stdin)
        config = input_data['config']
        process_limits = ProcessLimits(config)
        process_limits.enable()

        sandbox = Sandbox(config)
        code = input_data['code']
        locals = input_data.get('locals')
        globals = input_data.get('globals')
        try:
            result = sandbox._execute(code, globals, locals)
        finally:
            process_limits.disable()

        output_data = {'result': result}
        if 'globals' in input_data:
            del globals['__builtins__']
            output_data['globals'] = globals
        if 'locals' in input_data:
            output_data['locals'] = locals
    except BaseException, err:
        output_data = {'error': err}
        print(open("/proc/%s/maps" % os.getpid()).read())
        raise
    if redirect_stdout:
        output_data['stdout'] = sys.stdout.getvalue()
    pickle.dump(output_data, output)

def child_call(wpipe, sandbox, func, args, kw):
    process_limits = ProcessLimits(sandbox.config)
    try:
        process_limits.enable()
        try:
            result = sandbox._call(func, args, kw)
        finally:
            process_limits.disable()
        data = {'result': result}
    except BaseException, err:
        data = {'error': err}
    output = os.fdopen(wpipe, 'wb')
    pickle.dump(data, output)
    output.flush()
    output.close()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

if __name__ == "__main__":
    execute_child()

