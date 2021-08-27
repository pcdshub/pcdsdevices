865 ccm-rework
#################

API Changes
-----------
- N/A

Features
--------
- Add a ``status`` method to ``BaseInterface`` to return the device's status
  string. This is useful for recording device status in the elog.

Device Updates
--------------
- Change ``CCM`` from a ``InOutPositioner`` to a normal device with a
  ``LightpathMixin`` interface. Being a positioner that contained a bunch
  of other positioners, methods like ``move`` were extremely ambiguous
  and confusing. The ``insert`` and ``remove`` methods are re-implemented
  as they are useful enough to keep.
- Split ``CCMCalc`` into ``CCMEnergy`` and ``CCMEnergyWithVernier`` to
  make the code easier to follow
- Remove unused ``CCMCalc`` feature to move to wavelength or theta
  to make the code simpler to debug
- Add aliases to the ``CCM`` for each of the motors.
- Adjust the ``CCM`` status to be identical to that from the old python code.
- Add functions and PVs to kill and home the ``CCM`` alio
- Calculate intermediate quantities in the ``CCM`` energy calc and make them
  available in both the status and as read-only signals.

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Add missing docstrings in the ``ccm`` module where appropriate.
- Add doc kwarg to all components in the ``ccm`` module.
- Add type hints to all method signatures in the ``ccm`` module.
- Adjust the ``CCM`` unit tests appropriately.

Contributors
------------
- zllentz
