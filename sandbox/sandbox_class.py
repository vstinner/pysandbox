from .config import SandboxConfig

class Sandbox:
    PROTECTIONS = []

    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = SandboxConfig()
        self.protections = [protection() for protection in self.PROTECTIONS] 

    def __enter__(self):
        for protection in self.protections:
            protection.enable(self)

    def __exit__(self, type, value, traceback):
        for protection in self.protections:
            protection.disable(self)

