988 api-mds-clarify
###################

API Changes
-----------
- ``MultiDerivedSignal`` and ``MultiDerivedSignalRO`` calculation functions
  (``calculate_on_get`` and ``calculate_on_put``) now take new signatures.
  Calculation functions may be either methods on an ``ophyd.Device`` (with
  ``self``) or standalone functions with the following signature:

  .. code::

    calculate_on_get(mds: MultiDerivedSignal, items: SignalToValue) -> OphydDataType
    calculate_on_put(mds: MultiDerivedSignal, value: OphydDataType) -> SignalToValue


Features
--------
- N/A

Device Updates
--------------
- ``AT2L0`` has been updated due to underlying ``MultiDerivedSignal`` API
  changes.
- ``TwinCATStatePositioner`` has been updated due to underlying
  ``MultiDerivedSignal`` API changes.

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- klauer
