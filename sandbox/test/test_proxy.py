from sandbox import HAVE_CSANDBOX, Sandbox, SandboxError
from sandbox.test import createSandbox, createSandboxConfig, SkipTest

def test_object_proxy_read():
    class Person:
        __doc__ = 'Person doc'

        def __str__(self):
            "Convert to string"
            return "str"

        def __repr__(self):
            return "repr"

        def __hash__(self):
            return 42

    person = Person()

    def testPerson(person):
        assert person.__doc__ == 'Person doc'

        assert person.__str__() == "str"
        assert person.__repr__() == "repr"
        assert person.__hash__() == 42

        assert person.__str__.__name__ == "__str__"
        assert person.__str__.__doc__ == "Convert to string"

    testPerson(person)

    sandbox = createSandbox()
    sandbox.call(testPerson, person)

class Person:
    def __init__(self, name):
        self.name = name

def test_object_proxy_setattr():
    # Attribute
    def setAttr(person):
        person.name = "victor"

    person = Person("haypo")
    sandbox = createSandbox()
    try:
        sandbox.call(setAttr, person)
    except SandboxError, err:
        assert str(err) == 'Read only object'
    else:
        assert False

    setAttr(person)
    assert person.name == "victor"

def test_object_proxy_delattr():
    # Delete attribute
    def delAttr(person):
        del person.name

    person = Person("haypo")
    sandbox = createSandbox()
    try:
        sandbox.call(delAttr, person)
    except SandboxError, err:
        assert str(err) == 'Read only object'
    else:
        assert False

    delAttr(person)
    assert hasattr(person, 'name') == False

def test_object_proxy_dict():
    if not HAVE_CSANDBOX:
        # restricted python blocks access to instance.__dict__
        raise SkipTest("require _sandbox")

    # Dictionary
    def setDict(person):
        person.__dict__['name'] = "victor"

    person = Person("haypo")
    sandbox = createSandbox()
    try:
        sandbox.call(setDict, person)
    except SandboxError, err:
        assert str(err) == 'Read only object'
    else:
        assert False

    setDict(person)
    assert person.name == "victor"

def test_proxy_module():
    def check_proxy_module():
        from sys import modules
        try:
            modules['sys']
        except SandboxError, err:
            assert str(err) == "Unable to proxy a value of type <type 'module'>"
        else:
            assert False

    config = createSandboxConfig()
    config.allowModule('sys', 'modules')
    sandbox = Sandbox(config)
    sandbox.call(check_proxy_module)

