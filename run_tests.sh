#!/bin/bash
PYTHON=python
PYVER=$(python -c 'import sys; print("%s.%s" % sys.version_info[:2])')
set -x
$PYTHON setup.py build
PYTHONPATH=$(cd build/lib.*-$PYVER/; pwd) $PYTHON tests.py
