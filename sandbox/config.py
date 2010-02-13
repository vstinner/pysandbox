from os.path import realpath
from os import sep as path_sep
import sys

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
    def __init__(self, *features):
        # builtins whitelist: see CleanupBuiltins
        self.builtins_whitelist = set()

        # open() whitelist: see safe_open()
        self.open_whitelist = set()

        # import whitelist: see safe_import()
        self.import_whitelist = {}

        # list of enabled features
        self.features = set()

        for feature in features:
            self.enable(feature)

    def enable(self, feature):
        # If you add a new feature, update the README documentation
        if feature in self.features:
            return
        self.features.add(feature)

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
            self.builtins_whitelist.add('exit')
        elif feature == 'traceback':
            # change allowModule() behaviour
            pass
        elif feature in ('stdin', 'stdout', 'stderr'):
            self.allowModule('sys', feature)
            # ProtectStdio.enable() use also these features
        elif feature == 'site':
            license_filename = findLicenseFile()
            if license_filename:
                self.allowPath(license_filename)
            self.allowModuleSourceCode('site')
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
            self.allowModule('pydoc', 'help')
        elif feature == 'debug_sandbox':
            self.enable('traceback')
            self.allowModuleSourceCode('sandbox')
        else:
            self.features.remove(feature)
            raise ValueError("Unknown feature: %s" % feature)

    def allowModule(self, name, *attributes):
        if name in self.import_whitelist:
            self.import_whitelist[name] |= set(attributes)
        else:
            self.import_whitelist[name] = set(attributes)
        self.allowModuleSourceCode(name)

    def allowPath(self, path):
        real = realpath(path)
        if path.endswith(path_sep) and not real.endswith(path_sep):
            # realpath() eats trailing separator
            # (eg. /sym/link/ -> /real/path).
            #
            # Restore the suffix (/real/path -> /real/path/) to avoid
            # matching unwanted path (eg. /real/path.evil.path).
            real += path_sep
        self.open_whitelist.add(real)

    def allowModuleSourceCode(self, name):
        """
        Allow reading the module source.
        Do nothing if traceback is disabled.
        """
        if 'traceback' not in self.features:
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

    def createOptparseOptions(self, parser):
        parser.add_option("--features", help="List of enabled features separated by a comma",
            type="str")
        parser.add_option("--allow-path",
            help="Allow reading files from PATH",
            action="append", type="str")

    def useOptparseOptions(self, options):
        if options.features:
            for feature in options.features.split(","):
                feature = feature.strip()
                if not feature:
                    continue
                self.enable(feature)
        if options.allow_path:
            for path in options.allow_path:
                self.allowPath(path)

