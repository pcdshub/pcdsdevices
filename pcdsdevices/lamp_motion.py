"""
LAMP Motion Classes

This module contains classes related to the TMO-LAMP Motion System
"""

from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class LAMP(BaseInterface, Device):
    """
    LAMP Motion Class

    This class controls motors fixed to the LAMP Motion system for the LAMP
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
    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_jet_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    gas_needle_x = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    gas_needle_y = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    gas_needle_z = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')

    sample_paddle_x = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    sample_paddle_y = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
    sample_paddle_z = Cpt(BeckhoffAxis, ':MMS:09', kind='normal')
