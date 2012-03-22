from sandbox import Protection
import sys
from os.path import dirname
import os

class ClearImport(Protection):
    def __init__(self):
        # Only allow the standard library
        self.safe_path = (dirname(os.__file__),)

    def enable(self, sandbox):
        #self.modules = dict(sys.modules)
        self.path_importer_cache = dict(sys.path_importer_cache)
        self.path = list(sys.path)
        self.meta_path = list(sys.meta_path)
        self.path_hooks = list(sys.path_hooks)

        #sys.modules.clear()
        sys.path_importer_cache.clear()
        del sys.path[:]
        sys.path.extend(sandbox.config.sys_path)
        del sys.meta_path[:]
        del sys.path_hooks[:]

    def disable(self, sandbox):
        #sys.modules.clear()
        #sys.modules.update(self.modules)
        sys.path_importer_cache.clear()
        sys.path_importer_cache.update(self.path_importer_cache)

        del sys.path[:]
        sys.path.extend(self.path)
        del sys.meta_path[:]
        sys.meta_path.extend(self.meta_path)
        del sys.path_hooks[:]
        sys.path_hooks.extend(self.path_hooks)

        #self.modules = None
        self.path = None
        self.meta_path = None


