Base Classes
############
:class:`.pcdsdevices.Device` looks for a keyword ``db_info`` upon
instantiation.  This captures keyword information that come from the ``happi``
databae and saves it underneath the :attr:`.db` attribute as
:class:`.HappiData`. 

.. autoclass:: pcdsdevices.device.HappiData

Loading from happi
------------------
There are a few helper functions in ``pcdsdevices`` that facilitate loading
from ``happi``

.. autofunction:: pcdsdevices.happireader.read_happi

.. autofunction:: pcdsdevices.happireader.construct_device

MPS Information
---------------
.. automodule:: pcdsdevices.epics.mps

.. autoclass:: pcdsdevices.epics.MPS
   :members:
