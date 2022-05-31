"""
LAMP Motion Classes

This module contains classes related to the TMO-LAMP Motion System
"""

from ophyd import Component as Cpt
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class CVMI(BaseInterface, GroupDevice):
    """
    CVMI Motion Class

    This class controls motors fixed to the CVMI Motion system for the IP1
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

    sample_paddle = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')

    # LEDs
    led1_name = Cpt(EpicsSignal, ':LED:01:NAME', kind='normal')
    led1_pct = Cpt(EpicsSignal, ':LED:01:ILL:PCT', kind='normal')
    led1_pwr = Cpt(EpicsSignalRO, ':LED:01:PWR', kind='normal')

    led2_name = Cpt(EpicsSignal, ':LED:02:NAME', kind='normal')
    led2_pct = Cpt(EpicsSignal, ':LED:02:ILL:PCT', kind='normal')
    led2_pwr = Cpt(EpicsSignalRO, ':LED:02:PWR', kind='normal')


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
