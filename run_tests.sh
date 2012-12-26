#!/bin/bash
set -e

rm -rf build

TESTED=""
for PYVER in 2.5 2.6 2.7; do
    PYTHON=python$PYVER
    $PYTHON -c pass 1>/dev/null 2>&1 || continue
    $PYTHON setup.py build
    PYTHONPATH=$(cd build/lib.*-$PYVER/; pwd) $PYTHON tests.py --raise
    if [ ! -z "$TESTED" ]; then
        TESTED="$TESTED, $PYVER"
    else
        TESTED="$PYVER"
    fi
done

echo "pysandbox tested on Python $TESTED"
