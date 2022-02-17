"""
Delay generator class

This module contains classes related to the SRS DG645 delay generator.
"""

from time import sleep

from ophyd import Device
from ophyd import Component as Cpt
from ophyd import EpicsSignalRO
from ophyd import EpicsSignal

from .interface import BaseInterface


CHANNELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'T0']


class Dg_channel(BaseInterface, Device):
    """
    Delay generator single channel class

    Parameters
    ----------
    prefix: str
        Base PV for the delay generator channel

    name: str
        Alias of the channel
    """
    delay = Cpt(EpicsSignal, 'DelayAO', kind='hinted')
    delay_rbk = Cpt(EpicsSignalRO, 'DelaySI', kind='normal')
    reference = Cpt(EpicsSignal, 'ReferenceMO', kind='normal')

    tab_component_names = True
    tab_whitelist = ['set_reference', 'get_str']

    def get(self):
        """ The readback is a string formatted as"<REF> + <DELAY>" """
        return float(self.delay_rbk.get().split("+")[1])

    def get_str(self):
        return self.delay_rbk.get()

    def set(self, new_delay):
        return self.delay.set(new_delay)

    def set_reference(self, new_ref):
        if new_ref.upper() not in CHANNELS:
            raise ValueError(f'New reference must be one of {CHANNELS}')
        else:
            self.reference.set(new_ref)
            sleep(0.05)
            print(f'New setting for {self.name}: {self.get_str()}')


"""
Basic delay generator class. Collection of channels A to H.

Parameters
----------
prefix: str
    Base PV for the delay generator.

name: str
    Alias for the device
"""
channel_cpts = {}
for channel in CHANNELS[:-1]:
    channel_cpts[f'ch{channel}'] = Cpt(
        Dg_channel, f":{channel.lower()}", name=f"ch{channel}"
        )
channel_cpts['tab_component_names'] = True
Dg = type('Dg', (BaseInterface, Device), channel_cpts)
