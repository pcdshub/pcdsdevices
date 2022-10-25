1069 fix_lp_sub_spam
####################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- When initializing the lightpath summary signal from a happi load,
  guard against bad input_branches or output_branches.
  This stops us from spamming the terminal when loading from a db without
  input_branches and output_branches.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
