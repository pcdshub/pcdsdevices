"""
Module for controlling LEDs or fiber-lites.
To be paired with FB_LED function block.
"""


import logging

from ophyd import Component as Cpt

from .device import Device
from .signal import PytmcSignal

logger = logging.getLogger(__name__)


class LightControl(Device):
    """
    Basic control and readback PVs for LEDs/Fiber-Lites.
    These include illumination percentage, power ON/OFF,
    and a naming string field.
    """

    # LED variables
    desc = Cpt(
        PytmcSignal, ':NAME',
        io='io',
        kind='normal',
        string=True
    )

    pct = Cpt(
        PytmcSignal, ':ILL:PCT',
        kind='normal',
        io='io',
        doc='Illuminator percentage'
    )

    pwr = Cpt(
        PytmcSignal, ':PWR',
        kind='normal',
        io='i',
        doc='Illuminator power boolean (ON/OFF)'
    )
