PCDS Devices
############

Ophyd presents a uniform set of abstractions for EPICS devices. While many
devices can be represented as generic ``EpicsMotor`` and ``AreaDetector``
objects, quite a few devices are specific to LCLS. This repository holds all of
these unique devices as well as additional tools to help aid the creation of
custom devices for specific applications.


Device Types
------------
.. autosummary::
    :nosignatures:
    :toctree: generated
    
    pcdsdevices.device_types.Attenuator
    pcdsdevices.daq.Daq
    pcdsdevices.device_types.EpicsMotor
    pcdsdevices.device_types.GateValve
    pcdsdevices.device_types.IPM
    pcdsdevices.device_types.OffsetMirror
    pcdsdevices.device_types.PIM
    pcdsdevices.device_types.PulsePicker
    pcdsdevices.device_types.Slits
    pcdsdevices.device_types.Stopper
    pcdsdevices.device_types.XFLS

.. toctree::
   :maxdepth: 1
   :caption: Developer Documentation 
   :hidden:
    
   state.rst
   inout.rst
