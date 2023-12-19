=========
Shortcuts
=========
.. currentmodule:: pcdsdevices.interface

A number of spec-like shortcuts are included in most ``pcdsdevices`` classes.
These shortcuts are geared for the ``ipython`` command-line experience, and
their API is considered unstable: they may change at any time at a user's
request (though we'll do our best not to break anything).
To this end, unlike the built-in methods, these methods do not return
:class:`~ophyd.status.Status` objects and are allowed to create arbitrary
terminal readback and prints.

All ``pcdsdevices`` with a ``move`` command and a ``position`` property
implement the `MvInterface`.

.. autosummary::

    ~MvInterface.mv
    ~MvInterface.wm


All ``pcdsdevices`` that return `float` values for their ``position``
(e.g. motors but not state devices) implement the `FltMvInterface`:

.. autosummary::

    ~FltMvInterface.mvr
    ~FltMvInterface.umv
    ~FltMvInterface.umvr
