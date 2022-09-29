1028 enh_lp_mixin
#################

API Changes
-----------
- Converts LightpathMixin to the new Lightpath API, consilodating
  reporting into a single LightpathState Dataclass.  The lightpath
  subscription system has also been simplified by using an AggregateSignal
  to monitor all relevant components.

Features
--------
- N/A

Device Updates
--------------
- Updates LightpathMixin implementation to the new API for all
  existing lightpath-active devices.  This includes but is not limited to:

  - Mirrors
  - LODCMs
  - Attenuators


New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Adds happi containers that work with the new Lightpath interface.
  Notably, these containers allow input_branches and output_branches
  to be optional kwargs.  This lets these containers work with devices
  that both do and do not implement the Lightpath interface.

Contributors
------------
- tangkong
