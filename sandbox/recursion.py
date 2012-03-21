from __future__ import absolute_import
from sandbox import Protection
import sys

class SetRecursionLimit(Protection):
    def enable(self, sandbox):
        self.old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(sandbox.config.recusion_limit)

    def disable(self, sandbox):
        sys.setrecursionlimit(self.old_limit)

