1216 Fixing_Tpr_Bug_For_MultiDerivedSignals
#################

API Breaks
----------
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
- Previously, calculate_on_get/put functions used in MultiDerivedSignals in tpr classes were not accessing
  their attrs correctly and would throw KeyErrors when called
- Specifically, the name of the attr was being used as the key for items dictionary instead of the actual signal object
- Also added unit tests for these MultiDerivedSignals

Maintenance
-----------
- N/A

Contributors
------------
- KaushikMalapati
