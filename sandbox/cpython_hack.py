from ctypes import (c_void_p, sizeof, string_at, c_size_t, 
    Structure, POINTER, cast, c_int)
from ctypes import pythonapi
from struct import unpack
import sys

Py_REF_DEBUG = hasattr(sys, "gettotalrefcount")
Py_TRACE_REFS = Py_REF_DEBUG

NULL = 0

# Python 2.6 constant
CO_MAXBLOCKS = 20

Py_ssize_t = c_size_t
PyObject_p = c_void_p
PyObject_pp = POINTER(PyObject_p)

class PyObject_HEAD(Structure):
    if Py_TRACE_REFS:
        _fields_ = (
            ("_ob_next", c_void_p), # struct _object*
            ("_ob_prev", c_void_p), # struct _object*
        )
    else:
        _fields_ = tuple()
    _fields_ += (
	("ob_refcnt", Py_ssize_t),
        ("ob_type", c_void_p), # struct _typeobject*
    )
PyObject_HEAD_p = POINTER(PyObject_HEAD)

class PyTryBlock(Structure):
    _fields_ = (
        ("b_type", c_int),
        ("b_handler", c_int),
        ("b_level", c_int),
    )

class PyObject_VAR_HEAD(Structure):
    _fields_ = PyObject_HEAD._fields_ + (
        ("ob_size", Py_ssize_t),
    )

class PyFrameObject(Structure):
    # Python 2.6 attributes 
    _fields_ = PyObject_VAR_HEAD._fields_ + (
        ("f_back", c_void_p),
        ("f_code", PyObject_p),
        ("f_builtins", PyObject_p),
        ("f_globals", PyObject_p),
        ("f_locals", PyObject_p),
        ("f_valuestack", PyObject_pp),
        ("f_stacktop", PyObject_pp),
        ("f_trace", PyObject_p),
        ("f_exc_type", PyObject_p),
        ("f_exc_value", PyObject_p),
        ("f_exc_traceback", PyObject_p),
        ("f_tstate", c_void_p),
        ("f_lasti", c_int),
        ("f_lineno", c_int),
        ("f_iblock", c_int),
        ("f_blockstack", PyTryBlock * CO_MAXBLOCKS),
        ("f_localsplus", PyObject_pp),
    )

# ob_refcnt, ob_type
sizeof_PyObject_HEAD = sizeof(Py_ssize_t) + sizeof(c_void_p)
if Py_TRACE_REFS:
    # _ob_next, _ob_prev
    sizeof_PyObject_HEAD += sizeof(c_void_p) * 2
sizeof_PyObject_VAR_HEAD = sizeof_PyObject_HEAD + sizeof(Py_ssize_t)

ssize_t = c_size_t

def cobject_address(obj):
    return id(obj)

def get_cobject(ob, type=None):
    if type is not None:
        type = POINTER(type)
    else:
        type = PyObject_HEAD_p
    ptr = cobject_address(ob)
    return cast(c_void_p(ptr), type)[0]

def Py_TYPE(ob):
    """
    Get ob->ob_type (pointer to the type object)
    """
    return get_cobject(ob).ob_type

class ClearFrameCache:
    def __init__(self, frame):
        self.frame = frame
        self.cframe = get_cobject(self.frame, PyFrameObject)

        # clear f_locals
        self.locals = frame.f_locals.copy()
        frame.f_locals.clear()

        # clear f_localsplus (LOAD_FAST/STORE_FAST cache)
        self.cache_size = 2 
        self.cache = []
        for index in xrange(self.cache_size):
            ptr = self.cframe.f_localsplus[index] 
            print "CLEAR CACHE[%s]=%s" % (index, ptr)
            pythonapi._PyObject_Dump(ptr)
            self.cache.append(ptr)
            self.cframe.f_localsplus[index] = cobject_address(42)

    def restore(self):
        # restore f_localsplus (LOAD_FAST/STORE_FAST cache)
        for index, ptr in enumerate(self.cache):
            self.cframe.f_localsplus[index] = ptr
        # restore f_locals
        self.frame.f_locals.update(self.locals)

