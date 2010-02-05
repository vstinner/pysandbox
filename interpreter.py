from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox, SandboxConfig
import readline

config = SandboxConfig()
config.enable('interpreter')
config.enable('regex')

from pprint import pprint
print "Sandbox config:"
pprint(config.__dict__)
print

with Sandbox(config):
    InteractiveConsole().interact("Try to break the sandbox!")

