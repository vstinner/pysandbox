from sandbox import USE_CSANDBOX, SandboxError
from sandbox.test import createSandbox, SkipTest

def test_read_objectproxy():
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

def test_modify_objectproxy():
    if not USE_CSANDBOX:
        raise SkipTest("require _sandbox")

    class Person:
        def __init__(self, name):
            self.name = name

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

    # Dictionary
    def setDict(person):
        person.__dict__['name'] = "victor"

    person = Person("haypo")
    try:
        sandbox.call(setDict, person)
    except SandboxError, err:
        assert str(err) == 'Read only object'
    else:
        assert False

    setDict(person)
    assert person.name == "victor"

