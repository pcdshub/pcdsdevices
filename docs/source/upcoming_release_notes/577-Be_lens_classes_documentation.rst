577 Be_lens_classes_documentation
#################

API Changes
-----------
- Changed the `read_lens` to open a normal file instead of a `.yaml` file, and to be able to read one lens set at the time from a file with multiple lens sets.
- Changed the `create_lens` methods to use a normal file instead of `.yaml` file, and also to be able to create a set with multiple sets of lens.


Features
--------
- Added a `set_lens_set` method to allow the user to choose what set from the file to use for calculations.

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Added more documentation to methods and LensStack class.
- Chaged from using functions defined in these classes to using the `pcdscalc.be_lens_calcs`

Contributors
------------
- cristinasewell
