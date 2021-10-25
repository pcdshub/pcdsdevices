============
Base Classes
============

Synchronized Axes
-----------------

The `SyncAxis` class is provided as a shortcut for creating classes that need
to move multiple positioners at the same time with the same scale. This is
useful for things like stands that have multiple motors.

You can create a class as:

.. code-block:: python

    class Parallel(SyncAxis):
        left = Cpt(EpicsMotor, ':01')
        right = Cpt(EpicsMotor, ':02')


There are different modes for how to keep the offset between the motors.  See
the `full API of SyncAxis <SyncAxis>` for more information.

Previous documentation indicated to use `SyncAxesBase`, but this has since been
deprecated and we no longer suggest for it to be used.


Offset Motor
------------

A pseudopositioner base class that supports adding an offset to an existing
motor is `OffsetMotorBase`.

Laser delay stages
------------------

pcdsdevices provides a laser delay stage base class that helps rescale a
physical axis to a time axis.

The optical laser travels along the motor's axis and bounces off a number of
mirrors, then continues to the destination. In this way, the path length of the
laser changes, which introduces a variable delay. This delay is a simple
multiplier based on the speed of light.

For more details, see `DelayBase` (`delay_class_factory`,
`delay_instance_factory`).

An "Interface" class is also provided which does not require subclassing.
See `DelayMotor` for more information.

.. code-block:: python

   stage = SynMotor(name="stage")
   delay = DelayMotor(motor=stage, name="delay")


Look-up Tables
--------------

pcdsdevices provides a base class for pseudo positioners which need a look-up
table to compute positions.

Currently it supports a single pseudo positioner and single "real" positioner,
which should be mapped to columns of a 2D numpy.ndarray ``table``.

See `LookupTablePositioner` for more information.


PV Positioners
--------------

pcdsdevices offers several flavors of "PV Positioners" - building on the
ophyd concept of `PVPositioner`.  These allow the user to group disparate
EPICS signals into a single ophyd device, in order to make it conform to the
same interface as a standard `EpicsMotor`.

The following options are available:

* `PVPositionerComparator` - a PV Positioner with a software done moving
  signal; i.e., you supply the comparison function to say when the motion has
  completed.
* `PVPositionerIsClose` - a PV Positioner that is considered done moving when
  the readback and setpoint are within a certain relative/absolute tolerance.
* `PVPositionerDone` - a PV positioner that is solely comprised of a setpoint
  signal and assumes motion has completed.
