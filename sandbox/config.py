from os.path import realpath

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
        elif feature == 'interpreter':
            self.enable('traceback')
            self.enable('stdin')
            self.enable('stdout')
            self.enable('stderr')
            self.enable('exit')
            self.allowModuleSourceCode('code')
            self.allowModuleSourceCode('site')
            self.allowModuleSourceCode('sandbox')
            self.allowModule('sys',
                'api_version', 'version', 'hexversion',
                'stdin', 'stdout', 'stderr')
            self.allowModule('pydoc', 'help')
        elif feature == 'traceback':
            # change allowModule() behaviour
            pass
        elif feature in ('stdin', 'stdout', 'stderr'):
            # see ProtectStdio.enable()
            pass
        else:
            self.features.remove(feature)
            raise ValueError("Unknown feature: %s" % feature)

    def allowModule(self, name, *attributes):
        if name in self.import_whitelist:
            self.import_whitelist[name] |= set(attributes)
        else:
            self.import_whitelist[name] = set(attributes)
        if 'traceback' in self.features:
            self.allowModuleSourceCode(name)

    def allowPath(self, path):
        path = realpath(path)
        self.open_whitelist.add(path)

    def allowModuleSourceCode(self, name):
        """
        Allow reading the module source.
        """
        module = __import__(name)
        for part in name.split(".")[1:]:
            module = getattr(module, part)
        try:
            filename = module.__file__
        except AttributeError:
            return
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

