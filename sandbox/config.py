from os.path import realpath, dirname

class SandboxConfig:
    def __init__(self):
        # builtins whitelist: see CleanupBuiltins
        self.builtins_whitelist = set()

        # open() whitelist: see safe_open()
        self.open_whitelist = set()

        # import whitelist: see safe_import()
        self.import_whitelist = {}

        # list of enabled features
        self.features = set()

    def enable(self, feature):
        if feature in self.features:
            return
        self.features.add(feature)

        if feature == 'regex':
            self.allowModule('re',
                    'compile', 'match', 'search', 'findall', 'finditer', 'split', 'sub', 'subn', 'escape',
                    'error',
                    'I', 'IGNORECASE',
                    'L', 'LOCALE',
                    'M', 'MULTILINE',
                    'S', 'DOTALL',
                    'X', 'VERBOSE')
            self.allowModule('sre_parse', 'parse')
        elif feature == 'exit':
            self.allowModule('sys', 'exit')
            self.builtins_whitelist.add('exit')
        elif feature == 'interpreter':
            self.enable('traceback')
            self.allowModuleSourceCode('code')
            self.allowModuleSourceCode('site')
            self.allowModuleSourceCode('sandbox')
            self.allowModule('sys',
                'api_version', 'version', 'hexversion',
                'stdin', 'stdout', 'stderr')
            self.allowModule('pydoc', 'help')

    def allowModule(self, name, *attributes):
        if name in self.import_whitelist:
            self.import_whitelist[name] |= set(attributes)
        else:
            self.import_whitelist[name] = set(attributes)
        if 'traceback' in self.features:
            self.allowModuleSourceCode(name)

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
        filename = realpath(filename)
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        if filename.endswith('__init__.py'):
            filename = filename[:-11]
        self.open_whitelist.add(filename)

