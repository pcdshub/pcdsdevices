"""
Von Hamos Motion Classes

This module contains classes related to the Von Hamos Spectrometer Motion System
"""

from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class VonHamos(BaseInterface, Device):
    """
    Von Hamos Beckhoff Motion Class

    This class controls Beckhoff motors fixed to the Von Hamos Spectrometer
    used in HXR hutches.

    Parameters
    ----------
    prefix : str
        Base PV for the Von Hamos motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    y = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
