848 create new VCN_OpenLoop device class
#################

API Breaks
----------
- N/A

Library Features
----------------
- N/A

Device Features
---------------
- N/A

New Devices
-----------
- VCN_OpenLoop: similar to VCN w/ the removal of 'open' and 'position_readback'
  commands. The 'state' member variable has been renamed to 'control_mode' and
  the associated doc string was been updated.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- jozamudi
