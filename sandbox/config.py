from __future__ import absolute_import
from os.path import realpath, sep as path_sep, dirname, join as path_join, exists, isdir
from sys import version_info
#import imp
import sys
from sandbox import (DEFAULT_TIMEOUT,
    HAVE_CSANDBOX, HAVE_CPYTHON_RESTRICTED, HAVE_PYPY)
try:
    # check if memory limit is supported
    import resource
except ImportError:
    resource = None

_UNSET = object()

# The os module is part of the Python standard library
# and it is implemented in Python
import os
PYTHON_STDLIB_DIR = dirname(os.__file__)
del os

def findLicenseFile():
    import os
    # Adapted from setcopyright() from site.py
    here = PYTHON_STDLIB_DIR
    for filename in ("LICENSE.txt", "LICENSE"):
        for directory in (path_join(here, os.pardir), here, os.curdir):
            fullname = path_join(directory, filename)
            if exists(fullname):
                return fullname
    return None

#def getModulePath(name):
#    """
#    Get the path of a module, as "import module; module.__file__".
#    """
#    parts = name.split('.')
#
#    search_path = None
#    for index, part in enumerate(parts[:-1]):
#        fileobj, pathname, description = imp.find_module(part, search_path)
#        module = imp.load_module(part, fileobj, pathname, description)
#        del sys.modules[part]
#        try:
#            search_path = module.__path__
#        except AttributeError:
#            raise ImportError("%s is not a package" % '.'.join(parts[:index+1]))
#        module = None
#
#    part = parts[-1]
#    fileobj, pathname, description = imp.find_module(part, search_path)
#    if fileobj is not None:
#        fileobj.close()
#    if part == pathname:
#        # builtin module
#        return None
#    if not pathname:
#        # special module?
#        return None
#    return pathname
#
def getModulePath(name):
    old_modules = sys.modules.copy()
    try:
        module = __import__(name)
        return getattr(module, '__file__', None)
    finally:
        sys.modules.clear()
        sys.modules.update(old_modules)

class SandboxConfig(object):
    def __init__(self, *features, **kw):
        """
        Usage:
         - SandboxConfig('stdout', 'stderr')
         - SandboxConfig('interpreter', cpython_restricted=True)

        Options:

         - use_subprocess=True (bool): if True, execute() run the code in
           a subprocess
         - cpython_restricted=False (bool): if True, use CPython restricted
           mode instead of the _sandbox module
        """
        self.recusion_limit = 50
        self._use_subprocess = kw.get('use_subprocess', True)
        if self._use_subprocess:
            self._timeout = DEFAULT_TIMEOUT
            if resource is not None:
                self._max_memory = 250 * 1024 * 1024
            else:
                self._max_memory = None
            # size in bytes of all input objects serialized by pickle
            self._max_input_size = 64 * 1024
            # size in bytes of the result serialized by pickle
            self._max_output_size = 64 * 1024
        else:
            self._timeout = None
            self._max_memory = None
            self._max_input_size = None
            self._max_output_size = None

        # open() whitelist: see safe_open()
        self._open_whitelist = set()

        # import whitelist dict: name (str) => [attributes, safe_attributes]
        # where attributes and safe_attributes are set of names (str)
        self._import_whitelist = {}

        # list of enabled features
        self._features = set()

        try:
            self._cpython_restricted = kw['cpython_restricted']
        except KeyError:
            if HAVE_CSANDBOX:
                # use _sandbox
                self._cpython_restricted = False
            elif HAVE_PYPY:
                self._cpython_restricted = False
            else:
                # _sandbox is missing: use restricted mode
                self._cpython_restricted = True
        else:
            if not self._cpython_restricted \
            and (not HAVE_CSANDBOX and not HAVE_PYPY):
                raise ValueError(
                    "unsafe configuration: the _sanbox module is missing "
                    "and the CPython restricted mode is disabled")

        if self._cpython_restricted and not HAVE_CPYTHON_RESTRICTED:
            raise ValueError(
                "Your Python version doesn't support the restricted mode")

        self._builtins_whitelist = set((
            # exceptions
            'ArithmeticError', 'AssertionError', 'AttributeError',
            'BufferError', 'BytesWarning', 'DeprecationWarning', 'EOFError',
            'EnvironmentError', 'Exception', 'FloatingPointError',
            'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError',
            'ImportWarning', 'IndentationError', 'IndexError', 'KeyError',
            'LookupError', 'MemoryError', 'NameError', 'NotImplemented',
            'NotImplementedError', 'OSError', 'OverflowError',
            'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError',
            'RuntimeWarning', 'StandardError', 'StopIteration', 'SyntaxError',
            'SyntaxWarning', 'SystemError', 'TabError', 'TypeError',
            'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError',
            'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning',
            'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError',
            # blocked: BaseException - KeyboardInterrupt - SystemExit (enabled
            #          by exit feature), Ellipsis,

            # constants
            'False', 'None', 'True',
            '__doc__', '__name__', '__package__', 'copyright', 'license', 'credits',
            # blocked: __debug__

            # types
            'basestring', 'bytearray', 'bytes', 'complex', 'dict', 'file',
            'float', 'frozenset', 'int', 'list', 'long', 'object', 'set',
            'str', 'tuple', 'unicode',
            # note: file is replaced by safe_open()

            # functions
            '__import__', 'abs', 'all', 'any', 'apply', 'bin', 'bool',
            'buffer', 'callable', 'chr', 'classmethod', 'cmp',
            'coerce', 'compile', 'delattr', 'dir', 'divmod', 'enumerate', 'eval', 'exit',
            'filter', 'format', 'getattr', 'globals', 'hasattr', 'hash', 'hex',
            'id', 'isinstance', 'issubclass', 'iter', 'len', 'locals',
            'map', 'max', 'min', 'next', 'oct', 'open', 'ord', 'pow', 'print',
            'property', 'range', 'reduce', 'repr',
            'reversed', 'round', 'setattr', 'slice', 'sorted', 'staticmethod',
            'sum', 'super', 'type', 'unichr', 'vars', 'xrange', 'zip',
            # blocked: execfile, input
            #          and raw_input (enabled by stdin feature), intern,
            #          help (from site module, enabled by help feature), quit
            #          (enabled by exit feature), reload
            # note: reload is useless because we don't have access to real
            #       module objects
            # note: exit is replaced by safe_exit() if exit feature is disabled
            # note: open is replaced by safe_open()
        ))
        if HAVE_PYPY:
            self._builtins_whitelist |= set((
                # functions
                'intern',
            ))
        if version_info >= (3, 0):
            self._builtins_whitelist |= set((
                # functions
                '__build_class__', 'ascii', 'exec',
            ))

        self.sys_path = (PYTHON_STDLIB_DIR,)

        for feature in features:
            self.enable(feature)

    def has_feature(self, feature):
        return (feature in self._features)

    @property
    def features(self):
        return self._features.copy()

    @property
    def use_subprocess(self):
        return self._use_subprocess

    def _get_timeout(self):
        return self._timeout
    def _set_timeout(self, timeout):
        if timeout:
            if not self._use_subprocess:
                raise NotImplementedError("Timeout requires the subprocess mode")
            self._timeout = timeout
        else:
            self._timeout = None
    timeout = property(_get_timeout, _set_timeout)

    def _get_max_memory(self):
        return self._max_memory
    def _set_max_memory(self, mb):
        if not self._use_subprocess:
            raise NotImplementedError("Max Memory requires the subprocess mode")
        self._max_memory = mb * 1024 * 1024
    max_memory = property(_get_max_memory, _set_max_memory)

    @property
    def max_input_size(self):
        return self._max_input_size

    @property
    def max_output_size(self):
        return self._max_output_size

    @property
    def import_whitelist(self):
        return dict((name, (tuple(value[0]), tuple(value[1])))
            for name, value in self._import_whitelist.iteritems())

    @property
    def open_whitelist(self):
        return self._open_whitelist.copy()

    @property
    def cpython_restricted(self):
        return self._cpython_restricted

    @property
    def builtins_whitelist(self):
        return self._builtins_whitelist.copy()

    def enable(self, feature):
        # If you add a new feature, update the README documentation
        if feature in self._features:
            return
        self._features.add(feature)

        if feature == 'regex':
            self.allowModule('re',
                'findall', 'split',
                'sub', 'subn', 'escape', 'I', 'IGNORECASE', 'L', 'LOCALE', 'M',
                'MULTILINE', 'S', 'DOTALL', 'X', 'VERBOSE',
            )
            self.allowSafeModule('re',
                'compile', 'finditer', 'match', 'search', '_subx', 'error')
            self.allowSafeModule('sre_parse', 'parse')
        elif feature == 'exit':
            self.allowModule('sys', 'exit')
            self._builtins_whitelist |= set((
                'BaseException',
                'KeyboardInterrupt',
                'SystemExit',
                # quit builtin is added by the site module
                'quit'))
        elif feature == 'traceback':
            # change allowModule() behaviour
            pass
        elif feature in ('stdout', 'stderr'):
            self.allowModule('sys', feature)
            # ProtectStdio.enable() use also these features
        elif feature == 'stdin':
            self.allowModule('sys', 'stdin')
            self._builtins_whitelist.add('input')
            self._builtins_whitelist.add('raw_input')
        elif feature == 'site':
            if 'traceback' in self._features \
            and (not self._cpython_restricted):
                license_filename = findLicenseFile()
                if license_filename:
                    self.allowPath(license_filename)
            self.allowModuleSourceCode('site')
        elif feature == 'help':
            self.enable('regex')
            self.allowModule('pydoc', 'help')
            self._builtins_whitelist.add('help')
        elif feature == 'future':
            self.allowModule('__future__',
                'all_feature_names',
                'absolute_import', 'braces', 'division', 'generators',
                'nested_scopes', 'print_function', 'unicode_literals',
                'with_statement')
        elif feature == 'unicodedata':
            self.allowModule('unicodedata',
                # C API is used for u'\N{ATOM SYMBOL}': Python have to be
                # allowed to import it because it cannot be used in the sandbox
                'ucnhash_CAPI',
                # other functions
                'bidirectional', 'category', 'combining', 'decimal',
                'decomposition', 'digit', 'east_asian_width', 'lookup',
                'mirrored', 'name', 'normalize', 'numeric',
                'unidata_version')
        elif feature == 'time':
            self.allowModule('time',
                'accept2dyear', 'altzone', 'asctime', 'clock', 'ctime',
                'daylight', 'mktime', 'strftime', 'time',
                'timezone', 'tzname')
            self.allowSafeModule('time',
               'gmtime', 'localtime', 'struct_time')
            # blocked: sleep(), strptime(), tzset()
        elif feature == 'datetime':
            self.allowModule('datetime',
                'MAXYEAR', 'MINYEAR')
            self.allowSafeModule('datetime',
                'date', 'datetime', 'time', 'timedelta', 'tzinfo')
        elif feature == 'math':
            self.allowModule('math',
                'acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh',
                'ceil', 'copysign', 'cos', 'cosh', 'degrees', 'e', 'exp',
                'fabs', 'factorial', 'floor', 'fmod', 'frexp', 'fsum', 'hypot',
                'isinf', 'isnan', 'ldexp', 'log', 'log10', 'log1p', 'modf',
                'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh',
                'trunc')
        elif feature == 'itertools':
            self.allowSafeModule('itertools',
                'chain', 'combinations', 'count', 'cycle', 'dropwhile',
                'groupby', 'ifilter', 'ifilterfalse', 'imap', 'islice', 'izip',
                'izip_longest', 'permutations', 'product', 'repeat', 'starmap',
                'takewhile', 'tee')
            # TODO, python 2.7/3.2: combinations_with_replacement, compress
        elif feature == 'random':
            self.enable('math')
            self.allowModule('__future__', 'division')
            self.allowModule('warnings', 'warn')
            self.allowModule('types', 'MethodType', 'BuiltinMethodType')
            self.allowModule('os', 'urandom')
            self.allowModule('binascii', 'hexlify')
            self.allowSafeModule('_random', 'Random')
            self.allowModule('random',
                # variate
                'betavariate', 'expovariate', 'gammavariate', 'lognormvariate',
                'normalvariate', 'paretovariate', 'vonmisesvariate',
                'weibullvariate',
                # others
                'choice', 'gauss', 'getrandbits', 'randint', 'random',
                'randrange', 'sample', 'shuffle', 'triangular', 'uniform')
                # blocked: getstate, jumpahead, seed, setstate
            self.enable('hashlib')
        elif feature == 'hashlib':
            self.allowSafeModule('hashlib',
                'md5',
                'sha1',
                'sha224',
                'sha256',
                'sha384',
                'sha512')
            self.allowSafeModule('_hashlib',
                'openssl_md5',
                'openssl_sha1',
                'openssl_sha224',
                'openssl_sha256',
                'openssl_sha384',
                'openssl_sha512')
        elif feature == 'codecs':
            self.allowModule('codecs',
                'lookup', 'CodecInfo',
                'utf_8_encode', 'utf_8_decode',
                'utf_16_be_encode', 'utf_16_be_decode',
                'charmap_encode', 'charmap_decode')
            if version_info >= (2, 6):
                self.allowModule('codecs',
                    'utf_32_be_encode', 'utf_32_be_decode')
            self.allowSafeModule('codecs',
                'ascii_encode', 'ascii_decode',
                'latin_1_encode', 'latin_1_decode',
                'Codec', 'BufferedIncrementalDecoder',
                'IncrementalEncoder', 'IncrementalDecoder',
                'StreamWriter', 'StreamReader',
                'make_identity_dict', 'make_encoding_map')
        elif feature == 'encodings':
            self.enable('codecs')
            self.allowModule('encodings', 'aliases')
            self.allowModule('encodings.ascii', 'getregentry')
            self.allowModule('encodings.latin_1', 'getregentry')
            self.allowModule('encodings.utf_8', 'getregentry')
            self.allowModule('encodings.utf_16_be', 'getregentry')
            if version_info >= (2, 6):
                self.allowModule('encodings.utf_32_be', 'getregentry')
            if version_info < (3, 0):
                self.allowModule('encodings.rot_13', 'getregentry')
        else:
            self._features.remove(feature)
            raise ValueError("Unknown feature: %s" % feature)

    def allowModule(self, name, *attributes):
        if name in self._import_whitelist:
            self._import_whitelist[name][0] |= set(attributes)
        else:
            self._import_whitelist[name] = [set(attributes), set()]
        self.allowModuleSourceCode(name)

    def allowSafeModule(self, name, *safe_attributes):
        if name in self._import_whitelist:
            self._import_whitelist[name][1] |= set(safe_attributes)
        else:
            self._import_whitelist[name] = [set(), set(safe_attributes)]
        self.allowModuleSourceCode(name)

    def allowPath(self, path):
        if self._cpython_restricted:
            raise ValueError("open_whitelist is incompatible with the CPython restricted mode")
        real = realpath(path)
        if path.endswith(path_sep) and not real.endswith(path_sep):
            # realpath() eats trailing separator
            # (eg. /sym/link/ -> /real/path).
            #
            # Restore the suffix (/real/path -> /real/path/) to avoid
            # matching unwanted path (eg. /real/path.evil.path).
            real += path_sep
        self._open_whitelist.add(real)

    def allowModuleSourceCode(self, name):
        """
        Allow reading the module source.
        Do nothing if traceback is disabled.
        """
        if ('traceback' not in self._features) or self._cpython_restricted:
            # restricted mode doesn't allow to open any file
            return

        filename = getModulePath(name)
        if not filename:
            return
        if filename.endswith('.pyc') or filename.endswith('.pyo'):
            # file.pyc / file.pyo => file.py
            filename = filename[:-1]
        if isdir(filename) and not filename.endswith(path_sep):
            # .../encodings => .../encodings/
            filename += path_sep
        self.allowPath(filename)

    @staticmethod
    def createOptparseOptions(parser, default_timeout=_UNSET):
        if default_timeout is _UNSET:
           default_timeout = DEFAULT_TIMEOUT
        parser.add_option("--features",
            help="List of enabled features separated by a comma",
            type="str")
        if HAVE_CPYTHON_RESTRICTED:
            parser.add_option("--restricted",
                help="Use CPython restricted mode (less secure) instead of _sandbox",
                action="store_true")
        parser.add_option("--disable-subprocess",
            help="Don't run untrusted code in a subprocess (less secure)",
            action="store_true")
        parser.add_option("--allow-path",
            help="Allow reading files from PATH",
            action="append", type="str")
        if default_timeout:
            text = "Timeout (default: %.1f sec)" % default_timeout
        else:
            text = "Timeout (default: no timeout)"
        parser.add_option("--timeout",
            help=text, metavar="SECONDS",
            action="store", type="float", default=default_timeout)

    @staticmethod
    def fromOptparseOptions(options):
        kw = {}
        if HAVE_CPYTHON_RESTRICTED and options.restricted:
            kw['cpython_restricted'] = True
        if options.disable_subprocess:
            kw['use_subprocess'] = False
        config = SandboxConfig(**kw)
        if options.features:
            for feature in options.features.split(","):
                feature = feature.strip()
                if not feature:
                    continue
                config.enable(feature)
        if options.allow_path:
            for path in options.allow_path:
                config.allowPath(path)
        if config.use_subprocess:
            config.timeout = options.timeout
        return config

