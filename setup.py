#!/usr/bin/env python

# Todo list to prepare a release:
#  - run ./run_tests.sh
#  - check TODO if there is no more critical known bug
#  - do an audit of new features (see the ChangeLog)
#  - set version in sandbox/version.py
#  - set release date in the ChangeLog
#  - git commit -a
#  - git tag -a pysandbox-n
#  - git push --tags
#  - ./setup.py register sdist upload
#  - update the website
#
# After the release:
#  - set version to n+1
#  - add a new empty section in the changelog for version n+1
#  - git commit

from __future__ import with_statement
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

with open('README') as f:
    long_description = f.read().strip()

options = {
    'name': version.PACKAGE,
    'version': version.VERSION,
    'license': version.LICENSE,
    'description': 'Python sandbox',
    'long_description': long_description,
    'url': version.URL,
    'author': 'Victor Stinner',
    'author_email': 'victor.stinner@haypocalc.com',
    'ext_modules': [Extension('_sandbox', ['_sandbox/module.c'])],
    'classifiers': CLASSIFIERS,
    'packages': ('sandbox',),
}

setup(**options)

