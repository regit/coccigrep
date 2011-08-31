Presentation
------------

coccigrep provide an abstraction for running spatch in the scope of searching
for motiv in C source code.

There is two interesting classes:

 - :class:`coccigrep.CocciGrep`: main class that run the intensive task
 - :class:`coccigrep.CocciGrepConfig`: used to parse and get configuration value

To build a request:

 - Create a :class:`coccigrep.CocciGrep` instance
 - Call :func:`coccigrep.CocciGrep.setup` function to setup the search
 - Call :func:`coccigrep.CocciGrep.run` function to execute the search
 - Call :func:`coccigrep.CocciGrep.display` function to display the output of the search

Documentation du module
-----------------------

.. automodule:: coccigrep
   :members:
   :undoc-members:


