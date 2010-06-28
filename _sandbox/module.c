#include "Python.h"
#include "frameobject.h"

#define VERSION 1

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


static PyMethodDef sandbox_methods[] = {
    {"set_frame_builtins", set_frame_builtins, METH_VARARGS, 
     PyDoc_STR("set_frame_builtins(frame, builtins) -> None")},
    {"set_interp_builtins", set_interp_builtins, METH_VARARGS, 
     PyDoc_STR("set_interp_builtins(builtins) -> None")},
    {NULL,              NULL}           /* sentinel */
};

PyDoc_STRVAR(module_doc,
"_sandbox module.");

PyMODINIT_FUNC
init_sandbox(void)
{
    PyObject *m, *version;

    m = Py_InitModule3("_sandbox", sandbox_methods, module_doc);
    if (m == NULL)
        return;

    version = PyInt_FromLong(VERSION);
    PyModule_AddObject(m, "version", version);
}

