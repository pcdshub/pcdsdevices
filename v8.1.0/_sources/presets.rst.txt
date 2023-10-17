================
Preset Positions
================
.. currentmodule:: pcdsdevices.interface

All ``pcdsdevices`` objects that involve moving positioners across a
continuum of positions can save preset positions. See `Presets` for a
full API description, or stay here for the user guide.


Creating a Preset
-----------------
A device that can save and load presets will have a ``presets`` attribute.
This is the interface that is used to create new presets. The module is
configurable to have differing presets catagories, and these are typically
used to have "permanent" and "temporary" presets, and in ``hutch-python``
are laid out as such:

================================= ==================================================
          Method                                   Description
================================= ==================================================
add_hutch(name, value[, comment]) Add a permenant preset
add_exp(name, value[, comment])   Add a temporary preset
add_hutch_here(name[, comment])   Add a permenant preset with this spot as the value
add_exp_here(name[, comment])     Add a temporary preset with this spot as the value
================================= ==================================================


Using a Preset
--------------
After a preset is created, you can use the preset using three special methods.
These will be added directly to the object, not to the ``presets`` attribute:

============================== ==========================================
          Method                             Description
============================== ==========================================
mv_presetname([timeout, wait]) Move to this preset position
umv_presetname([timeout])      Move to thie preset position and update
wm_presetname()                Check the offset from this preset position
============================== ==========================================


Manage Existing Presets
-----------------------
You can see all existing presets via checking ``my_motor.presets.positions``.
In `IPython`, this will show you all the current presets. You can also use
this ``presets.positions`` object to manage the set positions. Each attribute
is an instance of `PresetPosition` that can be managed. See `PresetPosition`
for the full API.


Configuring Presets
-------------------
Presets are configured in ``hutch-python`` to use ``add_hutch`` and ``add_exp``
as the preset-adding methods, with the ``add_hutch`` method saving to a hutch
directory and ``add_exp`` saving to an experiment directory. This can be
changed for other applications using the `setup_preset_paths` method.
This method must be called for the presets to be saved and loaded.
