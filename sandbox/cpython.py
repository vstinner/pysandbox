from __future__ import absolute_import
from sandbox import HAVE_CSANDBOX
if HAVE_CSANDBOX:
    from _sandbox import dictionary_of
else:
    from ctypes import pythonapi, POINTER, py_object

    _get_dict = pythonapi._PyObject_GetDictPtr
    _get_dict.restype = POINTER(py_object)
    _get_dict.argtypes = [py_object]
    del pythonapi, POINTER, py_object

    def dictionary_of(ob):
        dptr = _get_dict(ob)
        return dptr.contents.value

