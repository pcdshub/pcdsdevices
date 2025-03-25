"""
DREAM Motion Classes

This module contains classes related to the TMO-DREAM Motion System
"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface
from .light_control import LightControl


class DREAM(BaseInterface, GroupDevice):
    """
    DREAM Motion Class

    This class controls motors fixed to the DREAM Motion system for the IP1
    endstation in TMO. It also controls LED rings for the endstation.

    Parameters
    ----------
    prefix : str
        Base PV for the DREAM motion system
    desc : str
        Description field for LED.
    pct : str
        Illumination percentage of a particular endstation LED.
    pwr : str
        ON/OFF powered boolean of a particular endstation LED.
    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components

    chamber_y = Cpt(BeckhoffAxis, ':MC:MMS:Y', kind='normal')
    coil_roll = Cpt(BeckhoffAxis, ':COIL:MMS:ROLL', kind='normal')
    coil_yaw  = Cpt(BeckhoffAxis, ':COIL:MMS:YAW', kind='normal')



    gas_jet_x = Cpt(BeckhoffAxis, ':GSJP:MMS:X', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':GSJP:MMS:Z', kind='normal')

    gas_nozzle_x = Cpt(BeckhoffAxis, ':GSJN:MMS:X', kind='normal')
    gas_nozzle_y = Cpt(BeckhoffAxis, ':GSJN:MMS:Y', kind='normal')
    gas_nozzle_z = Cpt(BeckhoffAxis, ':GSJN:MMS:Z', kind='normal')

