"""
CVMI Motion Classes for bootstrap experiment only

The bootstrap experiment is for early March 2025
This module contains classes related to the TMO-LAMP Motion System
"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class CVMI(BaseInterface, GroupDevice):
    """
    CVMI Motion Class

    This class controls motors fixed to the CVMI Motion system for the IP1
    endstation in TMO. It also controls LED rings for the endstation.

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system
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
    flow_cell_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    flow_cell_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    flow_cell_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')
    flow_cell_R = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')


class KTOF(BaseInterface, GroupDevice):
    """
    KTOF Motion Class

    This class controls motors fixed to the KTOF Motion system for the IP1
    endstation in TMO.

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    spec_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    spec_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    spec_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')
