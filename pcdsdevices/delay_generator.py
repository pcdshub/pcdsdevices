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
TRIGGER_SOURCES = {
    '0': 'Internal',
    '1': 'Ext ^edge',
    '2': 'Ext ~edge',
    '3': 'SS ext ^edge',
    '4': 'SS ext ~edge',
    '5': 'Single Shot',
    '6': 'Line'
}
TRIGGER_INHIBITS = {
    '0': 'Off',
    '1': 'Triggers',
    '2': 'AB',
    '3': 'AB,CD',
    '4': 'AB,CD,EF',
    '5': 'AB,CD,EF,GH'
}


class DgChannel(BaseInterface, Device):
    """
    Delay generator single channel class

    Parameters
    ----------
    prefix: str
        Base PV for the delay generator channel

    name: str
        Alias of the channel
    """
    delay = Cpt(EpicsSignal, 'DelaySI', write_pv='DelayAO', kind='hinted')
    #delay = Cpt(EpicsSignal, 'DelayAO', kind='hinted')
    #delay_rbk = Cpt(EpicsSignalRO, 'DelaySI', kind='normal')
    reference = Cpt(EpicsSignal, 'ReferenceMO', kind='normal')

    tab_component_names = True
    tab_whitelist = ['set_reference', 'get_str']

    def get(self):
        """
        The readback is a string formatted as"<REF> + <DELAY>".
        Returns the <DELAY> as a float
        """
        return float(self.delay.get().split("+")[1])

    def get_str(self):
        """ Returns the full <REF> + <DELAY> string. """
        return self.delay.get()

    def set(self, new_delay):
        return self.delay.set(new_delay)

    def set_reference(self, new_ref):
        if new_ref.upper() not in CHANNELS:
            raise ValueError(f'New reference must be one of {CHANNELS}')
        else:
            self.reference.set_and_wait(new_ref)
            print(f'Setting for {self.name}: {self.get_str()}')


class DelayGeneratorBase(BaseInterface, Device):
    """
    Delay generator class. Collection of channels A to H.

    Parameters
    ----------
    prefix: str
        Base PV for the delay generator.

    name: str
        Alias for the device
    """
    trig_source = Cpt(EpicsSignal, ':triggerSourceMO', kind='config')
    trig_source_rbk = Cpt(EpicsSignal, ':triggerSourceMI', kind='config')
    trig_inhibit = Cpt(EpicsSignal, ':triggerInhibitMO', kind='config')
    trig_inhibit_rbk = Cpt(EpicsSignal, ':triggerInhibitMI', kind='config')

    tab_component_names = True
    tab_whitelist = ['print_trigger_sources', 'get_trigger_source',
                     'set_trigger_source', 'print_trigger_inhibit',
                     'get_trigger_inhibit',
                     'set_trigger_inhibit']

    @staticmethod
    def print_trigger_sources():
        for ii, source in TRIGGER_SOURCES.items():
            print(f'{ii}: {source}')

    def get_trigger_source(self):
        n = self.trig_source_rbk.get()
        val = TRIGGER_SOURCES[str(n)]
        return f'{val} ({n})'

    def set_trigger_source(self, new_val):
        self.trig_source.set_and_wait(new_val)
        print(f'Trigger source: {self.get_trigger_source()}')
        return

    @staticmethod
    def print_trigger_inhibit():
        for ii, inhibit in TRIGGER_INHIBITS.items():
            print(f'{ii}: {inhibit}')

    def get_trigger_inhibit(self):
        n = self.trig_inhibit_rbk.get()
        val = TRIGGER_INHIBITS[str(n)]
        return f'{val} ({n})'

    def set_trigger_inhibit(self, new_val):
        self.trig_inhibit.set_and_wait(new_val)
        print(f'Trigger inhibit: {self.get_trigger_inhibit()}')
        return


channel_cpts = {}
for channel in CHANNELS[:-1]:
    channel_cpts[f'ch{channel}'] = Cpt(
        DgChannel, f":{channel.lower()}", name=f"ch{channel}"
        )

DelayGenerator = type('DelayGenerator', (DelayGeneratorBase, ), channel_cpts)
Dg = DelayGenerator
