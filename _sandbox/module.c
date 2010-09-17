#include "Python.h"
#include "frameobject.h"

/**
 * Version history:
 *  - Version 2: add dictionary_of() function
 *  - Version 1: initial version
 */
#define VERSION 2

#if PY_MAJOR_VERSION >= 3
# define PYTHON3
#endif

static newfunc code_new = NULL;
static PyObject *sandbox_error = NULL;

static PyObject *
set_error_class(PyObject *self, PyObject *args)
{
    PyObject *error;

    if (!PyArg_ParseTuple(args, "O:set_error_class", &error))
        return NULL;

    Py_XDECREF(sandbox_error);
    Py_INCREF(error);
    sandbox_error = error;
    Py_RETURN_NONE;
}

static PyObject *
set_frame_builtins(PyObject *self, PyObject *args)
{
    PyFrameObject *frame;
    PyObject *builtins;
    if (!PyArg_ParseTuple(args, "OO:set_frame_builtins", &frame, &builtins))
        return NULL;
    Py_XDECREF(frame->f_builtins);
    Py_INCREF(builtins);
    frame->f_builtins = builtins;
    Py_RETURN_NONE;
}

static PyObject *
set_interp_builtins(PyObject *self, PyObject *args)
{
    PyObject *builtins;
    PyThreadState *tstate;
    PyInterpreterState *interp;

    if (!PyArg_ParseTuple(args, "O:set_interp_builtins", &builtins))
        return NULL;

    tstate = PyThreadState_GET();
    interp = tstate->interp;

    Py_XDECREF(interp->builtins);
    Py_INCREF(builtins);
    interp->builtins = builtins;
    Py_RETURN_NONE;
}

static PyObject *
code_new_raise(PyTypeObject *type, PyObject *args, PyObject *kw)
{
    PyErr_SetString(sandbox_error, "code() blocked by the sandbox");
    return NULL;
}

static PyObject *
disable_code_new(PyObject *self)
{
    PyCode_Type.tp_new = code_new_raise;
    Py_RETURN_NONE;
}

static PyObject *
restore_code_new(PyObject *self)
{
    PyCode_Type.tp_new = code_new;
    Py_RETURN_NONE;
}

static PyObject *
dictionary_of(PyObject *self, PyObject *args)
{
    PyObject *obj, **dict_ptr, *dict;
    PyTypeObject *type;

    if (!PyArg_ParseTuple(args, "O:dictionary_of", &obj))
        return NULL;

    if (PyType_Check(obj)) {
        type = (PyTypeObject*)obj;
        if (type->tp_dict == NULL) {
            if(PyType_Ready(type) < 0)
                return NULL;
        }
    }

    dict_ptr = _PyObject_GetDictPtr(obj);
    if (dict_ptr == NULL)
        goto error;
    dict = *dict_ptr;
    if (dict == NULL)
        goto error;
    Py_INCREF(dict);
    return dict;

error:
    PyErr_SetString(sandbox_error, "Object has no dict");
    return NULL;
}

static PyMethodDef sandbox_methods[] = {
    {"set_error_class", set_error_class, METH_VARARGS,
     PyDoc_STR("set_error_class(error_class) -> None")},
    {"set_frame_builtins", set_frame_builtins, METH_VARARGS,
     PyDoc_STR("set_frame_builtins(frame, builtins) -> None")},
    {"set_interp_builtins", set_interp_builtins, METH_VARARGS,
     PyDoc_STR("set_interp_builtins(builtins) -> None")},
    {"disable_code_new", (PyCFunction)disable_code_new, METH_NOARGS,
     PyDoc_STR("disable_code_new() -> None")},
    {"restore_code_new", (PyCFunction)restore_code_new, METH_NOARGS,
     PyDoc_STR("restore_code_new() -> None")},
    {"dictionary_of", dictionary_of, METH_VARARGS,
     PyDoc_STR("dictionary_of(obj) -> dict")},
    {NULL,              NULL}           /* sentinel */
};

PyDoc_STRVAR(module_doc,
"_sandbox module.");

#ifdef PYTHON3
static struct PyModuleDef sandbox_module = {
    PyModuleDef_HEAD_INIT,
    "_sandbox",
    module_doc,
    -1,
    sandbox_methods,
    NULL,
    NULL,
    NULL,
    NULL
};
#endif

PyMODINIT_FUNC
#ifdef PYTHON3
PyInit__sandbox(void)
#else
init_sandbox(void)
#endif
{
    PyObject *m, *version;

    Py_INCREF(PyExc_ValueError);
    sandbox_error = PyExc_ValueError;

#ifdef PYTHON3
    m = PyModule_Create(&sandbox_module);
    if (m == NULL)
        return NULL;
#else
    m = Py_InitModule3("_sandbox", sandbox_methods, module_doc);
    if (m == NULL)
        return;
#endif

    code_new = PyCode_Type.tp_new;

#ifdef PYTHON3
    version = PyLong_FromLong(VERSION);
#else
    version = PyInt_FromLong(VERSION);
#endif
    PyModule_AddObject(m, "version", version);
#ifdef PYTHON3
    return m;
#endif
}

