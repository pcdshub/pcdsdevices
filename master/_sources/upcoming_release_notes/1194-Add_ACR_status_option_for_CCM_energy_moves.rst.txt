1194 Add ACR status option for CCM energy moves
#################

API Breaks
----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Add a CCMEnergyWithACRStatus class to ccm.py
- Add a energy_with_acr_status instance to CCM
- Update BeamEnergyRequest argument from bunch to pv_index to better reflect the broader use cases.
  A backward compatible warning is now returned if the old bunch kwarg is used.
- Update atol in BeamEnergyRequestNoWait to 0.5 (was 5). This is needed for self-seeding

New Devices
-----------
- Add a convenience decorator to re-arg a function in utils.py

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- vespos
