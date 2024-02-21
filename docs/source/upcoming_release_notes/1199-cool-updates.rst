1199 cool-updates
#################

API Breaks
----------
- N/A

Features
--------
-

Device Updates
--------------
- in `atm.py` add `flow_meter` to `ArrivalTimeMonitor`
- in `attenuator.py` add `flow_meter` to `AttenuatorSXR_Ladder`
- in `attenuator.py` add `flow_meter` to `AttenuatorSXR_LadderTwoBladeLBD`
- in `device_types.py` add `WaveFrontSensorTargetCool` , `WaveFrontSensorTargetFDQ`
- in `mirror.py` add flow sensor variable to `FFMirror`
- in `wfs.py` add `flow_meter` to `WaveFrontSensorTarget`

New Devices
-----------
- add class `PhotonCollimator` to readout `flow_switch` in new module `pc.py`
- add class `WaveFrontSensorTargetFDQ` to read out `flow_meter`
- add class `MFXATM` in `atm.py`

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- nrwslac
