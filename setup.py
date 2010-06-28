#!/usr/bin/env python

# Todo list to prepare a release:
#  - set version in sandbox/version.py
#  - set release date in the ChangeLog
#  - git tag -a pysandbox-n
#  - git push
#  - ./setup.py register sdist upload
#  - update the website
#
# After the release:
#  - set version to n+1
#  - add a new empty section in the changelog for version n+1
#  - git commit

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
    'author': 'Victor Stinner',
    'author_email': 'victor.stinner@haypocalc.com',
    'ext_modules': [Extension('_sandbox', ['_sandbox/module.c'])],
    'classifiers': CLASSIFIERS,
    'packages': ('sandbox',),
}

setup(**options)

