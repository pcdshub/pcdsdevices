"""
Class to handle USB encoders
"""

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from .interface import BaseInterface


class USBEncoder(BaseInterface, Device):
    """
    USB encoder class

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

    tab_whitelist = ['pos', 'set_zero', 'set_zero_with_stage',
                     'scale', 'offset']

    def __init__(self, prefix, *, name, stage=None, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.stage = stage

    def set_zero(self):
        """ Resets the encoder counts to 0 """
        self.zero.put(1)

    def set_zero_with_stage(self):
        """
        Resets the encoder counts to 0 and sets the stage offset
        so that its position is also 0.
        """
        self.zero.put(1)
        if (
            self.stage is not None or
            hasattr(self.stage, 'set_current_position')
        ):
            self.stage.set_current_position(0)
            print(f'Reset encoder {self.name} and axis {self.stage.name} to 0')
        else:
            print('No stage associated with that encoder,')
            print('or stage is not settable.\n')
            print('Resetting encoder only.')
        return
