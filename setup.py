#!/usr/bin/env python
from distutils.core import setup, Extension
import imp

version = imp.load_source('version', 'sandbox/version.py')

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: C',
    'Programming Language :: Python',
    'Topic :: Security',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

options = {
    'name': version.PACKAGE,
    'version': version.VERSION,
    'license': version.LICENSE,
    'url': version.URL,
    'ext_modules': [Extension('_sandbox', ['_sandbox/module.c'])],
    'classifiers': CLASSIFIERS,
    'packages': ('sandbox',),
}

setup(**options)

