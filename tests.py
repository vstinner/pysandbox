#!/usr/bin/env python
from sandbox import HAVE_CSANDBOX
from sys import version_info
from sandbox.test import SkipTest, createSandboxConfig
from sandbox.test.tools import getTests

def parseOptions():
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [options]")
    parser.add_option("--raise",
        help="Don't catch exception",
        dest="raise_exception",
        action="store_true")
    parser.add_option("--debug",
        help="Enable debug mode (enable stdout and stderr features)",
        action="store_true")
    parser.add_option("-k", "--keyword",
        help="Only execute tests with name containing KEYWORD",
        type='str')
    options, argv = parser.parse_args()
    if argv:
        parser.print_help()
        exit(1)
    return options

def main():
    global createSandboxConfig

    options = parseOptions()
    createSandboxConfig.debug = options.debug

    if not HAVE_CSANDBOX:
        print("WARNING: _sandbox module is missing")
        print

    # Get all tests
    all_tests = getTests(globals(), options.keyword)

    # Run tests
    nerror = 0
    if version_info < (2, 6):
        base_exception = Exception
    else:
        base_exception = BaseException
    for func in all_tests:
        name = '%s.%s()' % (func.__module__.split('.')[-1], func.__name__)
        try:
            func()
        except SkipTest, skip:
            print("%s: skipped (%s)" % (name, skip))
        except base_exception, err:
            nerror += 1
            print("%s: FAILED! %r" % (name, err))
            if options.raise_exception:
                raise
        else:
            print "%s: ok" % name

    # Exit
    from sys import exit
    print
    if nerror:
        print "%s ERRORS!" % nerror
        exit(1)
    else:
        print "%s tests succeed" % len(all_tests)
        exit(0)

if __name__ == "__main__":
    main()

