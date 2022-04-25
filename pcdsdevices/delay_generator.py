"""
Delay generator class

This module contains classes related to the SRS DG645 delay generator.
"""

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd.utils.epics_pvs import set_and_wait

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
    delay = Cpt(EpicsSignal, 'DelayAO', kind='hinted')
    delay_str = Cpt(EpicsSignalRO, 'DelaySI', kind='normal')
    reference = Cpt(EpicsSignal, 'ReferenceMO', kind='normal',
                    doc='Reference channel from which the delay taken.')

    tab_component_names = True
    tab_whitelist = ['set', 'set_reference', 'get_str']

    def get_str(self):
        """ Returns the full <REF> + <DELAY> string. """
        return self.delay_str.get()

    def set(self, new_delay, **kwargs):
        return self.delay.set(new_delay, **kwargs)

    def set_reference(self, new_ref):
        if new_ref.upper() not in CHANNELS:
            raise ValueError(f'New reference must be one of {CHANNELS}')
        else:
            set_and_wait(self.reference, new_ref)
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
    trig_source = Cpt(EpicsSignal, ':triggerSourceMI',
                      write_pv=':triggerSourceMO',
                      kind='config')
    trig_inhibit = Cpt(EpicsSignal, ':triggerInhibitMI',
                       write_pv=':triggerInhibitMO',
                       kind='config')

    tab_component_names = True
    tab_whitelist = ['print_trigger_sources', 'get_trigger_source',
                     'set_trigger_source', 'print_trigger_inhibit',
                     'get_trigger_inhibit', 'set_trigger_inhibit']

    @staticmethod
    def print_trigger_sources():
        for ii, source in TRIGGER_SOURCES.items():
            print(f'{ii}: {source}')

    def get_trigger_source(self):
        n = self.trig_source.get()
        val = TRIGGER_SOURCES[str(n)]
        return f'{val} ({n})'

    def set_trigger_source(self, new_val):
        set_and_wait(self.trig_source, new_val)
        print(f'Trigger source: {self.get_trigger_source()}')
        return

    @staticmethod
    def print_trigger_inhibit():
        for ii, inhibit in TRIGGER_INHIBITS.items():
            print(f'{ii}: {inhibit}')

    def get_trigger_inhibit(self):
        n = self.trig_inhibit.get()
        val = TRIGGER_INHIBITS[str(n)]
        return f'{val} ({n})'

    def set_trigger_inhibit(self, new_val):
        set_and_wait(self.trig_inhibit, new_val)
        print(f'Trigger inhibit: {self.get_trigger_inhibit()}')
        return


channel_cpts = {}
for channel in CHANNELS[:-1]:
    channel_cpts[f'ch{channel}'] = Cpt(
        DgChannel, f":{channel.lower()}", name=f"ch{channel}"
        )

DelayGenerator = type('DelayGenerator', (DelayGeneratorBase, ), channel_cpts)
Dg = DelayGenerator
