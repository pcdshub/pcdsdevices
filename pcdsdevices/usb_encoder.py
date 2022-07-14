"""
Class to handle USB encoders
"""

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from .interface import BaseInterface


class USBEncoder(BaseInterface, Device):
    """
    Delay generator single channel class

    Parameters
    ----------
    prefix: str
        Base PV of the USB encoder

    name: str
        USB encoder name
    """
    zero = Cpt(EpicsSignal, ':ZEROCNT', kind='omitted')
    pos = Cpt(EpicsSignal, ':POSITION', kind='hinted')
    scale = Cpt(EpicsSignal, ':SCALE', kind='config')
    offset = Cpt(EpicsSignal, ':OFFSET', kind='config')

    tab_whitelist = ['pos', 'set_zero', 'scale', 'offset']

    def set_zero(self):
        """ Resets the encoder counts to 0 """
        self.zero.put(1)
