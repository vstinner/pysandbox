from __future__ import with_statement
from sandbox import Sandbox

def test_valid_code():
    with Sandbox():
        assert 1+2 == 3

def test2():
    filename = __file__
    try:
        with Sandbox():
            with open(filename) as fp:
                fp.read()
        assert False, "open is still available!"
    except NameError, err:
        # open() is blocked by the sandbox
        assert str(err) == "global name 'open' is not defined"

    # open() is restored at sandbox exit
    with open(filename) as fp:
        fp.read()

