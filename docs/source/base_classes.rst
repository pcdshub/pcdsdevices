============
Base Classes
============

Synchronized Axes
-----------------
The `SyncAxesBase` class is provided as a shortcut for creating classes that
need to move multiple positioners at the same time with the same scale. This
is useful for things like stands that have multiple motors.

You can create a class as:

.. code-block:: python

    class Parallel(SyncAxesBase):
        left = Cpt(EpicsMotor, ':01')
        right = Cpt(EpicsMotor, ':02')

On the first move, these classes will save the offsets between the axes and
maintain them for all moves. This allows you to do things like move a table
with a constant tilt. You can manually save offsets using the ``save_offests``
method. By default, the position of the combined axes will be the smallest of
the composite positions, but this can be configured for other behavior.

See the `full api <SyncAxesBase>` for more information.
