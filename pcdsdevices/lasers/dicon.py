"""
Module for the DiCon fiber matrix switch used in the LCLS-II timing system.
"""

import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface
from pcdsdevices.variety import set_metadata

logger = logging.getLogger(__name__)


class DiconSwitch(BaseInterface, Device):
    """
    Class for controlling the DiCon fiber matrix switch.
    """

    chan1 = Cpt(EpicsSignal, ':getChan1', write_pv=':setOut1', kind='normal')
    chan2 = Cpt(EpicsSignal, ':getChan2', write_pv=':setOut2', kind='normal')
    chan3 = Cpt(EpicsSignal, ':getChan3', write_pv=':setOut3', kind='normal')
    chan4 = Cpt(EpicsSignal, ':getChan4', write_pv=':setOut4', kind='normal')
    chan5 = Cpt(EpicsSignal, ':getChan5', write_pv=':setOut5', kind='normal')
    chan6 = Cpt(EpicsSignal, ':getChan6', write_pv=':setOut6', kind='normal')
    chan7 = Cpt(EpicsSignal, ':getChan7', write_pv=':setOut7', kind='normal')
    chan8 = Cpt(EpicsSignal, ':getChan8', write_pv=':setOut8', kind='normal')

    version = Cpt(EpicsSignalRO, ':getVers', kind='config')

    error_str = Cpt(EpicsSignalRO, ':ErrStr', kind='config')
    error_num = Cpt(EpicsSignalRO, ':ErrorNum', kind='config')

    reset = Cpt(EpicsSignal, ':reset', kind='omitted')
    set_metadata(reset, dict(variety='command-proc', value=1))
