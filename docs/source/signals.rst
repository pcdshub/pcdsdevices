==============
Signal Classes
==============

.. currentmodule:: pcdsdevices.signal

AggregateSignal
---------------

:class:`AggregateSignal` is a signal class that allows you to calculate a
readback value from multiple other signals.

.. note::

    While this class requires subclassing in order to use, see also the
    :class:`MultiDerivedSignal` described below which can be more easily
    embedded in Device class hierarchies.

AggregateSignal handles configuring callbacks for you such that you will only
need to define a single calculation function in order to use it.

In your subclass, you should define a method such as:

.. code-block:: python

   def _calc_readback(self):
       """The calculation method you should implement."""
       # Access `._signals` here to calculate your value.
       return 10.0

The ``_signals`` attribute includes access to all signals you have defined
in the attribute list.  You should use this dictionary in order to calculate
the aggregated value.

Why not just use self.parent.cpt.get()?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* The AggregateSignal handles caching of values from callbacks.  It will only
  call your calculation method once everything is ready.
* Your signal should perform better and faster.  Network connections and EPICS
  Channel Access calls will not be necessary when using the provided cache.

Example
^^^^^^^

The following example defines a new Signal class called ``MySummingSignal``
which will sum its sibling component values "a" "b" and "c".  This assumes
it's used in a Device hierarchy with those components defined appropriately.

.. code-block:: python

    class MySummingSignal(AggregateSignal):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for attr_name in ["a", "b", "c"]:
                self.add_signal_by_attr_name(attr_name)

        def _calc_readback(self):
            return sum(sig.value for sig in self._signals.values())


    class MyDevice(ophyd.Device):
        a = Cpt(EpicsSignalRO, "A")
        b = Cpt(EpicsSignalRO, "B")
        c = Cpt(EpicsSignalRO, "C")
        summer = Cpt(MySummingSignal)
        # summer.get() is a.get() + b.get() + c.get()

AvgSignal
---------

:class:`AvgSignal` is a signal that calculates the rolling average of another
signal.

It uses ophyd subscriptions to populate a list of values of length ``average``.


Example
^^^^^^^

Acquire up to 10 data points from ``raw_signal``, perform the arithmetic mean,
and show its value in ``averaged``:

.. code-block:: python

    class MyDevice(ophyd.Device):
        raw_signal = Cpt(EpicsSignalRO, "OTHER:SIGNAL")
        averaged = Cpt(AvgSignal, signal="raw_signal", averages=10)

For this setting, after 10 data points, the first data point will be
overwritten.


PVStateSignal
-------------

:class:`PVStateSignal` is a signal class that implements the
:class:`PVStatePositioner` logic.  It's part of that class hierarchy, and
you should not have to use it yourself.

It uses :class:`AggregateSignal` in order to match up attributes from the
Device and map their values onto state positions.  A sample dictionary
that is usually in ``sig._state_logic`` might be:

.. code::

    {
      "signal_name": {
                       0: "OUT",
                       1: "IN",
                       2: "Unknown",
                       3: "defer"
                     }
    }

For more information, see :clas:`PVStatePositioner`.

PytmcSignal
-----------

.. note::

    Use this signal class if you are using
    [pytmc](https://github.com/pcdshub/pytmc/) in your device's corresponding
    EPICS IOC.

A :class:`PytmcSignal` uses information about the pytmc convention to determine
which signal class should be used automatically (either :class:`PytmcSignalRW`
and :class:`PytmcSignalRO`).

1. A symbol marked as "input" (or "ro") will have ``"_RBV"`` as a PV suffix.
   This will be mapped onto the :class:`PytmcSignalRW` signal class.
2. A symbol marked as "output" (or "rw") will **both** a setpoint PV and a
   readback PV, with ``"_RBV"`` as its suffix.
   This will be mapped onto the :class:`PytmcSignalRO` signal class.

Usage examples are in the following sections.

PytmcSignal for Outputs
^^^^^^^^^^^^^^^^^^^^^^^

Let's say you have a pragma as follows:

.. code-block::

    {attribute 'pytmc' := '
        pv: PREFIX:fValue
        io: output
    '}
    fValue: LREAL;


If found in a PLC program, this would create two top-level PVs:

* ``PREFIX:fValue`` - a setpoint value the user could caput to change the value of
fValue on the PLC

* ``PREFIX:fValue_RBV`` - a "Read-Back Value" (RBV) that reflects the current
  value held in fValue on the PLC.

You would use the following component to match this:

.. code-block:: python

    class MyDevice(ophyd.Device):
        value = ophyd.Component(
            PytmcSignal,
            ":fValue",    # <-- copy in ":fValue" from above
            io="output",  # <-- copy in "output" from above
            kind="normal",
            doc="Something useful about the 'fValue' signal"
        )

    dev = MyDevice("PREFIX", name="dev")

Once instantiated, your device will have a readable and writable
``PytmcSignalRW`` instance available from the ``.value`` attribute that talks
to the PLC ``fValue`` symbol.

The corresponding readback PV will be ``PREFIX:fValue_RBV`` (which you can
check with ``dev.value.pvname``) and the setpoint PV will be ``PREFIX:fValue``
(which you can check with ``dev.value.setpoint_pvname``).

PytmcSignal for Inputs
^^^^^^^^^^^^^^^^^^^^^^

Let's say you have a pragma as follows:

.. code-block::

    {attribute 'pytmc' := '
        pv: PREFIX:fValue
        io: input
    '}
    fValue: LREAL;


If found in a program, this would create a single top-level PVs:

* ``PREFIX:fValue`` - a "read-back value" that reflects the current value held
  in fValue on the PLC.

You would use the following component to match this:

.. code-block:: python

    class MyDevice(ophyd.Device):
        value = ophyd.Component(
            PytmcSignal,
            ":fValue",   # <-- copy in ":fValue" from above
            io="input",  # <-- copy in "input" from above
            kind="normal",
            doc="Something useful about the 'fValue' signal"
        )

    dev = MyDevice("PREFIX", name="dev")

Once instantiated, your device will have a read-only ``PytmcSignalRO`` instance
available from the ``.value`` attribute that talks to the PLC ``fValue``
symbol. The corresponding PV will be ``PREFIX:fValue_RBV`` (which you can check
with ``dev.value.pvname``).


MultiDerivedSignal and MultiDerivedSignalRO
-------------------------------------------

:class:`MultiDerivedSignal` and :class:`MultiDerivedSignalRO` are signal
classes that allow you to calculate a readback value from multiple other
signals.  Optionally, you can also take a single value from the user and
write to multiple other signals.

In short, these classes represent:

* Multiple source signals may be used to calculate a single
  ``MultiDerivedSignal`` value.  The calculation method used here is
  ``calculate_on_get`` in either a keyword argument to the signal or a method
  in a subclass.
* A single ``MultiDerivedSignal`` value, when ``set()``, may be used to write
  to those same signals. The calculation method used here is
  ``calculate_on_put`` in either a keyword argument to the signal or a method
  in a subclass.

A read-only MultiDerivedSignalRO
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This read-only example takes three signals from its parent device - "a", "b",
and "c" - and calculates a single value for them.

.. code-block:: python

    from pcdsdevices.type_hints import SignalToValue, OphydDataType

    class MdsReadOnlyExample(Device):
        def _on_get(self, mds: MultiDerivedSignal, items: SignalToValue) -> int:
            return sum(value for value in items.values())

        mds = Cpt(
            MultiDerivedSignalRO,
            attrs=["a", "b", "c"],
            calculate_on_get=_on_get,
        )
        a = Cpt(FakeEpicsSignal, "a")
        b = Cpt(FakeEpicsSignal, "b")
        c = Cpt(FakeEpicsSignal, "c")


.. code-block:: python

    >>> device.a.get()
    1
    >>> device.b.get()
    2
    >>> device.c.get()
    3
    >>> device.mds.get()
    6

A read-write MultiDerivedSignal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    class MdsReadWriteExample(Device):
        def _on_get(self, mds: MultiDerivedSignal, items: SignalToValue) -> int:
            return sum(value for value in items.values())

        def _on_put(self, mds: MultiDerivedSignal, value: OphydDataType) -> SignalToValue:
            to_write = float(value / 3.)
            return {
                self.parent.a: to_write,
                self.parent.b: to_write,
                self.parent.c: to_write,
            }

        mds = Cpt(
            MultiDerivedSignal,
            attrs=["a", "b", "c"],
            calculate_on_get=_on_get,
            calculate_on_put=_on_put,
        )
        a = Cpt(FakeEpicsSignal, "a")
        b = Cpt(FakeEpicsSignal, "b")
        c = Cpt(FakeEpicsSignal, "c")

.. code-block:: python

    >>> device.a.get()
    1
    >>> device.b.get()
    2
    >>> device.c.get()
    3
    >>> device.mds.get()
    6
    >> device.mds.set(24).wait()
    >>> device.a.get()
    8
    >>> device.b.get()
    8
    >>> device.c.get()
    8


UnitConversionDerivedSignal
---------------------------

:class:`UnitConversionDerivedSignal` is a derived signal class (i.e., one that
sources its information from another existing signal) which allows you to
change the units of the source signal into the units of your choice.

UnitConversionDerivedSignal Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    class UcdsExample(Device):
        original = Cpt(
            EpicsSignal,
            "PV",
            doc="PV with units of mm"
        )
        converted = Cpt(
            UnitConversionDerivedSignal,
            derived_from=orig,
            original_units='mm',
            derived_units='m',
            doc="Converted signal with units of 'm'"
        )

.. code-block:: python

    >>> device.original.get()
    10
    >>> device.converted.get()
    0.01


Put 0.1m and note that it's 100mm:

.. code-block:: python

    >> device.converted.put(0.1)
    >>> device.original.get()
    100


Advanced Signal Types
---------------------

There are additional signal types which will not be discussed in depth here
because their usage is uncommon or advanced.  For more details, see the
associated source code.

Fake Signal Types
^^^^^^^^^^^^^^^^^

Fake signal classes are used in the test suite.  For each of the signal classes
here, we provide a "fake" version of them.

Users should mostly be concerned with using ``make_fake_device`` on the
whole device and should not need to concern themselves with the details of
the fake signals directly.

InternalSignal
^^^^^^^^^^^^^^

:class:`InternalSignal` is a signal that is intended to be used internally
by a class and not presented to the end-user.  Similar to NotImplementedSignal,
it is generally an advanced signal type.


NotepadLinkedSignal
^^^^^^^^^^^^^^^^^^^

Creates a notepad metadata dict for usage by pcdsdevices-notepad.

NotImplementedSignal
^^^^^^^^^^^^^^^^^^^^

:class:`NotImplementedSignal` is primarily a placeholder for when you are
creating abstract ophyd device classes with the intent of subclassing and
updating them by way of :class:`~pcdsdevices.device.UpdateComponent`.

If the above doesn't make sense to you, you are probably not the target
audience of this.  Consider this an "advanced" signal type.


SignalEditMD, and EpicsSignalEditMD and EpicsSignalROEditMD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`SignalEditMD`, and :class:`EpicsSignalEditMD` and
:class:`EpicsSignalROEditMD` are variants of a signal type that allow you
to edit **metadata** coming from an existing signal.  This metadata
can include timestamps, units, enum information, and so on.
