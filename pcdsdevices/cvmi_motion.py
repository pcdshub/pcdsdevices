"""
LAMP Motion Classes

This module contains classes related to the TMO-LAMP Motion System
"""

from ophyd import Component as Cpt

from .device import Device, GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface
from .signal import PytmcSignal


class CvmiLED(Device):
    """
    Basic control and readback PVs for LED rings attached to the viewports
    on the vacuum chamber. These include illumination percentage,
    power ON/OFF, and a naming string field.
    """

    # LED variables
    desc = Cpt(PytmcSignal, ':NAME', io='io', kind='normal', string=True)
    pct = Cpt(PytmcSignal, ':ILL:PCT', kind='normal', io='io')
    pwr = Cpt(PytmcSignal, ':PWR', kind='normal', io='i')


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
        ON/OFF powered boolean of a particular endstation LED>
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
    led1 = Cpt(CvmiLED, ':LED:01')
    led2 = Cpt(CvmiLED, ':LED:02')


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
