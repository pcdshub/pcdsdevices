"""
Module for the various spectrometers.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class Kmono(Device):
    """
    K-edge Monochromator: Used for Undulator tuning and other experiments.

    This device has 3 main members: the crystal (xtal), the reticle
    (ret), and the diode (diode).

    The crystal angle motion has a pitch of 1000:1 HD of 0.6 mm. The crystal
    angle motor has 1000 steps. The crystal vertical motor moves the in and
    out of the beam path.

    The reticle horizontal motor allows for adjustments in the +/- x direction.
    The reticle vertical motor moves reticle in and out of the beam path in
    the +/- y direction.

    The diode horizontal motor allows for adjustments in the +/- x direction.
    The diode vertical motor moves reticle in and out of the beam path in
    the +/- y direction.
    """

    tab_component_names = True

    xtal_angle = Cpt(BeckhoffAxis, ':XTAL_ANGLE', kind='normal')
    xtal_vert = Cpt(BeckhoffAxis, ':XTAL_VERT', kind='normal')
    ret_horiz = Cpt(BeckhoffAxis, ':RET_HORIZ', kind='normal')
    ret_vert = Cpt(BeckhoffAxis, ':RET_VERT', kind='normal')
    diode_horiz = Cpt(BeckhoffAxis, ':DIODE_HORIZ', kind='normal')
    diode_vert = Cpt(BeckhoffAxis, ':DIODE_VERT', kind='normal')


class VonHamosCrystal(Device, BaseInterface):
    """Pitch, yaw, and translation motors for control of a single crystal"""

    tab_component_names = True

    pitch = Cpt(BeckhoffAxis, ':Pitch', kind='normal')
    yaw = Cpt(BeckhoffAxis, ':Yaw', kind='normal')
    trans = Cpt(BeckhoffAxis, ':Translation', kind='normal')


class VonHamosCommon(Device, BaseInterface):
    """Common motion for the motors controlling focus, energy, and rotation
       for a von Hamos spectrometer"""

    tab_component_names = True

    # Update PVs in IOC and change here to reflect
    f = FCpt(BeckhoffAxis, '{self._prefix_focus}', kind='normal')
    e = FCpt(BeckhoffAxis, '{self._prefix_energy}', kind='normal')
    rot = FCpt(BeckhoffAxis, '{self._prefix_rot}', kind='normal')

    def __init__(self, prefix, *, name, prefix_focus, prefix_energy,
                 prefix_rot, **kwargs):
        self._prefix_focus = prefix_focus
        self._prefix_energy = prefix_energy
        self._prefix_rot = prefix_rot
        super().__init__()


class VonHamos4Crystal(VonHamosCommon):
    """von Hamos spectrometer with common motors and four crystals"""

    c1 = Cpt(VonHamosCrystal, ':1', kind='normal')
    c2 = Cpt(VonHamosCrystal, ':2', kind='normal')
    c3 = Cpt(VonHamosCrystal, ':3', kind='normal')
    c4 = Cpt(VonHamosCrystal, ':4', kind='normal')
