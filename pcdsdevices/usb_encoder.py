"""
Class to handle USB encoders
"""

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from .interface import BaseInterface


class UsDigitalUsbEncoder(BaseInterface, Device):
    """
    Class for the USB encoder by US Digital.
    https://www.usdigital.com/products/accessories/interfaces/usb/usb4

    Parameters
    ----------
    prefix: str
        Base PV of the USB encoder

    name: str
        USB encoder name

    linked_axis: device
        Instance of the axis on which the encoder is mounted
    """
    zero = Cpt(EpicsSignal, ':ZEROCNT', kind='omitted')
    pos = Cpt(EpicsSignal, ':POSITION', kind='hinted')
    scale = Cpt(EpicsSignal, ':SCALE', kind='config')
    offset = Cpt(EpicsSignal, ':OFFSET', kind='config')

    tab_whitelist = ['pos', 'set_zero', 'set_zero_with_axis',
                     'scale', 'offset']

    def __init__(self, prefix, *, name, linked_axis=None, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.linked_axis = linked_axis

    def set_zero(self):
        """ Resets the encoder counts to 0 """
        self.zero.put(1)

    def set_zero_with_axis(self):
        """
        Resets the encoder counts to 0 and sets the linked_axis offset
        so that its position is also 0.
        """
        self.zero.put(1)
        if hasattr(self.linked_axis, 'set_current_position'):
            self.linked_axis.set_current_position(0)
            print(
                f'Reset encoder {self.name} and axis'
                f' {self.linked_axis.name} to 0.'
            )
        else:
            print(
                'No axis associated with that encoder,'
                'or axis is not settable.\n'
            )
            print('Reset encoder only.')
        return
