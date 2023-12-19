====================
IPython Tab Curation
====================
.. currentmodule:: pcdsdevices.interface

All devices in this package have optional namespace curation for their
``ipython`` tab completion. Most ``ophyd`` devices have a large number of
functions that are either not interesting to an interactive user or are
better off being left untouched in interactive sessions. To solve this,
every class has a whitelist of attributes that are findable via
``ipython`` tab completion. This feature is disabled by default,
but you can enable or disable this with simple commands:

.. autosummary::

   ~set_engineering_mode
   ~get_engineering_mode


For more information on how to add a tab completion whitelist to a class,
see the `BaseInterface` documentation.
