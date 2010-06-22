Default policy
==============

``f.func_globals`` is blocked

Don't support user functions?

::

  def plop():
      print "plop"
  => _print_ not defined

All names starting by "_"

exec() in __safe_builtins__
===========================

Blocked:

* ``compile()``
* ``iter()``
* ``type()``

