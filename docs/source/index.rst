PCDS Devices
############

Ophyd presents a uniform set of abstractions for EPICS devices. While many
devices can be represented as generic ``EpicsMotor`` and ``AreaDetector``
objects, quite a few devices are specific to LCLS. This repository holds all of
these unique devices as well as additional tools to help aid the creation of
custom devices for specific applications.

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Device Types

   epics_types.rst

.. toctree::
   :maxdepth: 1
   :caption: Developer Documentation 
   :hidden:
    
   state.rst
   inout.rst
