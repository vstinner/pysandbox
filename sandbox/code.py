from sandbox import Protection
from _sandbox import disable_code_new, restore_code_new

class DisableCode(Protection):
    def enable(self, sandbox):
        disable_code_new()

    def disable(self, sandbox):
        restore_code_new()

