"""
TMO MBES Motion Classes

This module contains classes related to the TMO-MBES Motion System
"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class MBES(BaseInterface, GroupDevice):
    """
    MBES Motion Class

    This class controls motors fixed to the MBES Motion system for the IP1
    endstation in TMO.

    Parameters
    ----------
    prefix : str
        Base PV for the MBES motion system
    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    magnetic_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    magnetic_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    magnetic_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    gas_jet_y = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')

    gas_needle_x = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    gas_needle_y = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
    gas_needle_z = Cpt(BeckhoffAxis, ':MMS:09', kind='normal')

    sample_paddle = Cpt(BeckhoffAxis, ':MMS:10', kind='normal')
