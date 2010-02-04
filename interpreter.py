from __future__ import with_statement
from code import InteractiveConsole
from sandbox import Sandbox
import readline

def create_options():
    from os.path import realpath, dirname
    from pprint import pprint
    options = {}
    options['open_whitelist'] = []
    def plop(name):
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
        options['open_whitelist'].append(filename)
    plop('code')
    plop('site')
    plop('sandbox')
    options['import_whitelist'] = {
        'sys': (
            'api_version', 'version', 'hexversion',
            'stdin', 'stdout', 'stderr',
            'exit'),
        'pydoc': ('help',),
        're': (
            'compile', 'match', 'search', 'findall', 'finditer', 'split', 'sub', 'subn', 'escape',
            'error',
            'I', 'IGNORECASE',
            'L', 'LOCALE',
            'M', 'MULTILINE',
            'S', 'DOTALL',
            'X', 'VERBOSE'),
        'sre_parse': ("parse",),
    }
    for module in options['import_whitelist']:
        plop(module)
    options['builtins_whitelist'] = ('exit',)
    print "Sandbox options:"
    pprint(options)
    print
    return options

with Sandbox(**create_options()):
    InteractiveConsole().interact("Try to break the sandbox!")

