from os.path import realpath, sep as path_sep, dirname, join as path_join, exists, isdir
from sys import version_info
#import imp
import sys

DEFAULT_TIMEOUT = 5.0

def findLicenseFile():
    # Adapted from setcopyright() from site.py
    import os
    here = dirname(os.__file__)
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

class SandboxConfig:
    def __init__(self, *features, **kw):
        """
        Usage:
         - SandboxConfig('stdout', 'stderr')
         - SandboxConfig('interpreter', cpython_restricted=True)
        """

        # open() whitelist: see safe_open()
        self._open_whitelist = set()

        # import whitelist dict: name (str) => [attributes, safe_attributes]
        # where attributes and safe_attributes are set of names (str)
        self._import_whitelist = {}

        # list of enabled features
        self._features = set()

        self._cpython_restricted = kw.get('cpython_restricted', False)

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
            'coerce', 'delattr', 'dir', 'divmod', 'enumerate', 'eval', 'exit',
            'filter', 'format', 'getattr', 'globals', 'hasattr', 'hash', 'hex',
            'id', 'isinstance', 'issubclass', 'iter', 'len', 'locals',
            'map', 'max', 'min', 'next', 'oct', 'open', 'ord', 'pow', 'print',
            'property', 'range', 'reduce', 'repr',
            'reversed', 'round', 'setattr', 'slice', 'sorted', 'staticmethod',
            'sum', 'super', 'type', 'unichr', 'vars', 'xrange', 'zip',
            # blocked: compile (enabled by code feature), execfile, input
            #          and raw_input (enabled by stdin feature), intern,
            #          help (from site module, enabled by help feature), quit
            #          (enabled by exit feature), reload
            # note: reload is useless because we don't have access to real
            #       module objects
            # note: exit is replaced by safe_exit()
            # note: open is replaced by safe_open()
        ))
        if version_info >= (3, 0):
            self._builtins_whitelist |= set((
                # functions
                '__build_class__', 'exec',
            ))

        # Timeout in seconds: use None to disable the timeout
        self.timeout = kw.get('timeout', DEFAULT_TIMEOUT)

        for feature in features:
            self.enable(feature)

    @property
    def features(self):
        return self._features.copy()

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
                'compile', 'match', 'search', 'findall', 'finditer', 'split',
                'sub', 'subn', '_subx', 'escape', 'I', 'IGNORECASE', 'L', 'LOCALE', 'M',
                'MULTILINE', 'S', 'DOTALL', 'X', 'VERBOSE',
                # FIXME: proxy() doesn't support class yet
                # 'error',
            )
            self.allowModule('sre_parse', 'parse')
        elif feature == 'exit':
            self.allowModule('sys', 'exit')
            self._builtins_whitelist |= set((
                'BaseException',
                'KeyboardInterrupt',
                'SystemExit',
                # quit builtin is added by the site module
                'quit'))
        elif feature == 'traceback':
            if self._cpython_restricted:
                raise ValueError("traceback feature is incompatible with the CPython restricted mode")
            # change allowModule() behaviour
        elif feature in ('stdout', 'stderr'):
            self.allowModule('sys', feature)
            # ProtectStdio.enable() use also these features
        elif feature == 'stdin':
            self.allowModule('sys', 'stdin')
            self._builtins_whitelist.add('input')
            self._builtins_whitelist.add('raw_input')
        elif feature == 'site':
            if 'traceback' in self._features:
                license_filename = findLicenseFile()
                if license_filename:
                    self.allowPath(license_filename)
            self.allowModuleSourceCode('site')
        elif feature == 'help':
            self.enable('regex')
            self.allowModule('pydoc', 'help')
            self._builtins_whitelist.add('help')
        elif feature == 'code':
            self._builtins_whitelist.add('compile')
        elif feature == 'interpreter':
            # "Meta" feature + some extras
            self.enable('traceback')
            self.enable('stdin')
            self.enable('stdout')
            self.enable('stderr')
            self.enable('exit')
            self.enable('site')
            self._builtins_whitelist.add('compile')
            self.allowModuleSourceCode('code')
            self.allowModule('sys',
                'api_version', 'version', 'hexversion', 'version_info')
        elif feature == 'debug_sandbox':
            self.enable('traceback')
            self.allowModule('sys', '_getframe')
            self.allowModuleSourceCode('sandbox')
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
        elif feature == 'codecs':
            self.allowModule('codecs',
                'lookup', 'CodecInfo',
                'ascii_encode', 'ascii_decode',
                'latin_1_encode', 'latin_1_decode',
                'utf_32_be_encode', 'utf_32_be_decode')
            self.allowSafeModule('codecs',
                'Codec', 'BufferedIncrementalDecoder',
                'IncrementalEncoder', 'IncrementalDecoder',
                'StreamWriter', 'StreamReader')
        elif feature == 'encodings':
            self.enable('codecs')
            self.allowModule('encodings', 'aliases')
            self.allowModule('encodings.ascii', 'getregentry')
            self.allowModule('encodings.latin_1', 'getregentry')
            self.allowModule('encodings.utf_8', 'getregentry')
            self.allowModule('encodings.utf_32_be', 'getregentry')
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
        if 'traceback' not in self._features:
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
    def createOptparseOptions(parser, default_timeout=DEFAULT_TIMEOUT):
        parser.add_option("--features",
            help="List of enabled features separated by a comma",
            type="str")
        parser.add_option("--restricted",
            help="Enable CPython restricted mode",
            action="store_true")
        parser.add_option("--allow-path",
            help="Allow reading files from PATH",
            action="append", type="str")
        if default_timeout is not None:
            text = "Timeout in seconds, use 0 to disable the timeout"
            text += " (default: %.1f seconds)" % default_timeout
        else:
            text = "Timeout in seconds (default: no timeout)"
        parser.add_option("--timeout",
            help=text,
            type="float", default=default_timeout)

    @staticmethod
    def fromOptparseOptions(options):
        kw = {}
        if options.restricted:
            kw['cpython_restricted'] = True
        if options.timeout:
            kw['timeout'] = options.timeout
        else:
            kw['timeout'] = None
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
        return config

