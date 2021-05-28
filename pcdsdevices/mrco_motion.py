"""
MRCO Motion Classes

This module contains classes related to the TMO-MRCO Motion System
"""

from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class MRCO(BaseInterface, Device):
    """
    MRCO Motion Class

    This class controls motors fixed to the MRCO Motion system for the IP1
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
    gas_nozzle_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_nozzle_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_nozzle_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    sample_paddle_x = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    sample_paddle_y = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    sample_paddle_z = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')
