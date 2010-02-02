from ctypes import pythonapi, POINTER, py_object

get_dict = pythonapi._PyObject_GetDictPtr
get_dict.restype = POINTER(py_object)
get_dict.argtypes = [py_object]

def dictionary_of(ob):
    dptr = get_dict(ob)
    return dptr.contents.value

