#include "Python.h"
#include "frameobject.h"

#define VERSION 1

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
    if (sandbox_error == NULL) {
        PyErr_SetString(PyExc_ValueError, "Sandbox error is not set");
        return NULL;
    }
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

