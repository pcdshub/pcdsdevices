"""
Module for the `KMONO` motion class
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt

from .epics_motor import BeckhoffAxis


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
