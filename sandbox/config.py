from os import sep as path_sep
from os.path import realpath
import sys

DEFAULT_TIMEOUT = 5.0

def findLicenseFile():
    # Adapted from setcopyright() from site.py
    import os
    here = os.path.dirname(os.__file__)
    for filename in ["LICENSE.txt", "LICENSE"]:
        for directory in (os.path.join(here, os.pardir), here, os.curdir):
            fullname = os.path.join(directory, filename)
            if os.path.exists(fullname):
                return fullname
    return None

class SandboxConfig:
    def __init__(self, *features, **kw):
        """
        Usage:
         - SandboxConfig('stdout', 'stderr')
         - SandboxConfig('interpreter', cpython_restricted=True)
        """

        # open() whitelist: see safe_open()
        self._open_whitelist = set()

        # import whitelist: see safe_import()
        self._import_whitelist = {}

        # list of enabled features
        self._features = set()

        self._cpython_restricted = kw.get('cpython_restricted', False)

        # Timeout in seconds: use None to disable the timeout
        self.timeout = kw.get('timeout', DEFAULT_TIMEOUT)

        for feature in features:
            self.enable(feature)

    @property
    def features(self):
        return self._features

    @property
    def import_whitelist(self):
        return self._import_whitelist

    @property
    def open_whitelist(self):
        return self._open_whitelist

    @property
    def cpython_restricted(self):
        return self._cpython_restricted

    def enable(self, feature):
        # If you add a new feature, update the README documentation
        if feature in self._features:
            return
        self._features.add(feature)

        if feature == 'regex':
            self.allowModule('re',
                'compile', 'match', 'search', 'findall', 'finditer', 'split',
                'sub', 'subn', 'escape', 'I', 'IGNORECASE', 'L', 'LOCALE', 'M',
                'MULTILINE', 'S', 'DOTALL', 'X', 'VERBOSE',
                # FIXME: proxy() doesn't support class yet
                # 'error',
            )
            self.allowModule('sre_parse', 'parse')
        elif feature == 'exit':
            self.allowModule('sys', 'exit')
        elif feature == 'traceback':
            if self._cpython_restricted:
                raise ValueError("traceback feature is incompatible with the CPython restricted mode")
            # change allowModule() behaviour
        elif feature in ('stdin', 'stdout', 'stderr'):
            self.allowModule('sys', feature)
            # ProtectStdio.enable() use also these features
        elif feature == 'site':
            if 'traceback' in self._features:
                license_filename = findLicenseFile()
                if license_filename:
                    self.allowPath(license_filename)
            self.allowModuleSourceCode('site')
        elif feature == 'help':
            self.allowModule('pydoc', 'help')
            self.enable('regex')
        elif feature == 'interpreter':
            # "Meta" feature + some extras
            self.enable('stdin')
            self.enable('stdout')
            self.enable('stderr')
            self.enable('exit')
            self.enable('site')
            self.allowModuleSourceCode('code')
            self.allowModule('sys',
                'api_version', 'version', 'hexversion')
        elif feature == 'debug_sandbox':
            self.enable('traceback')
            self.allowModule('sys', '_getframe')
            self.allowModuleSourceCode('sandbox')
        elif feature == 'future':
            self.allowModule('__future__',
                'absolute_import', 'braces', 'division', 'generators',
                'nested_scopes', 'print_function', 'unicode_literals',
                'with_statement')
        else:
            self._features.remove(feature)
            raise ValueError("Unknown feature: %s" % feature)

    def allowModule(self, name, *attributes):
        if name in self._import_whitelist:
            self._import_whitelist[name] |= set(attributes)
        else:
            self._import_whitelist[name] = set(attributes)
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
        old_sys_modules = sys.modules.copy()
        try:
            module = __import__(name)
            for part in name.split(".")[1:]:
                module = getattr(module, part)
            try:
                filename = module.__file__
            except AttributeError:
                return
        finally:
            sys.modules.clear()
            sys.modules.update(old_sys_modules)
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        if filename.endswith('__init__.py'):
            filename = filename[:-11]
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

