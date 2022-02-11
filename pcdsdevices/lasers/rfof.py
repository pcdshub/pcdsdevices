"""
Module for the RFoF systems used in the LCLS-II timing system.
"""

import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface

logger = logging.getLogger(__name__)


class CycleRfofRx(BaseInterface, Device):
    """
    Class for reading back the Cycle RFoF receiver PVs.
    """
    rf_temperature = Cpt(EpicsSignalRO, ':RFTEMPERATURE', kind='normal')
    rf_power = Cpt(EpicsSignalRO, ':RFPOWER', kind='normal')
    optical_power = Cpt(EpicsSignalRO, ':OPTICALPOWER', kind='normal')


class CycleRfofTx(CycleRfofRx):
    """
    Class for reading back the Cycle RFoF transmitter PVs.
    """
    # Transmitter adds a single control PV
    enable_laser = Cpt(EpicsSignal, ':ENABLELASER', kind='normal')
