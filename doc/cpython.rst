Python 2.x has a restriced mode. It is enabled when the builtins attribute of a
frame is different from the interpreter builtins. The restricted mode is used
by the Python rexec module.

``frame.f_restricted``: ``True if frame.builtins is not interpreter.builtins``

Restricted
----------

 * function:

   - block read/write: ``func_closure``, ``__closure__``, ``__globals__``

   - block write: ``func_doc``, ``__doc__``, ``__module__``

 * instance method:

   - block read/write: ``im_class``, ``im_func``, ``__func__``, ``im_self``, ``__self__``

 * method:

   - block read: ``__self__``

   - block write: ``__module__``

 * function:

   - block read/write: ``__dict__``, ``func_dict``, ``func_code``, ``__code__``,
     ``func_defaults``, ``__defaults__``

   - block write: ``__name__``, ``func_name``

 * class:

   - block read: ``__dict__``

   - block write: any attribute

 * instance:

   - block read/write: ``__dict__``

   - block write: ``__class__``

 * ``open()``

 * ``PyEval_GetRestricted``:

   - pickler: use ``copy_reg.dipatch_table``
