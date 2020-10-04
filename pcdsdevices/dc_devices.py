"""
Standard classes for L2SI DC power devices.
"""
import logging

from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class ICTChannel(Device):
    """
    Class to define a particular channel of the ICT.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant ICT.

    channel : str
        The output channel on the ICT, e.g. '1A', '3B', etc.
    """

    ch_current = FCpt(EpicsSignalRO, '{self.prefix}:Output{self._ch}:Current',
                      kind='hinted')
    ch_status = FCpt(EpicsSignal, '{self.prefix}:Output{self._ch}:GetState',
                     write_pv='{self.prefix}:Output{self._ch}:SetState',
                     kind='hinted', string=True)
    ch_name = FCpt(EpicsSignal, '{self.prefix}:Output{self._ch}.DESC',
                   kind='hinted')
    breaker_status = FCpt(EpicsSignalRO,
                          '{self.prefix}:Output{self._ch}:BreakerStatus',
                          kind='hinted', string=True)

    def __init__(self, prefix, channel, name='ICT_channel', **kwargs):
        self._ch = f'{channel.upper()}'
        super().__init__(prefix, name=name, **kwargs)

    def on(self):
        self.ch_status.put(0)

    def off(self):
        self.ch_status.put(1)

    def current(self):
        return self.ch_current.get()


class ICTBus(Device):
    """
    Class to define a current bus of the ICT.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant ICT.

    bus : str
        The output bus on the ICT, 'A' or 'B'.
    """

    bus_current = FCpt(EpicsSignalRO, '{self.prefix}:Bus{self._bus}:Current',
                       kind='hinted')
    bus_voltage = FCpt(EpicsSignalRO, '{self.prefix}:Bus{self._bus}:Voltage',
                       kind='hinted')
    bus_name = FCpt(EpicsSignal, '{self.prefix}:Bus{self._bus}.DESC',
                    kind='hinted')

    def __init__(self, prefix, bus, name='ICT_bus', **kwargs):
        self._bus = f'{bus.upper()}'
        super().__init__(prefix, name=name, **kwargs)

    def current(self):
        return self.bus_current.get()

    def voltage(self):
        return self.bus_voltage.get()


class ICT(BaseInterface, Device):
    """Complete ICT device with access to all buses and channels."""
    bus_A = FCpt(ICTBus, '{self.prefix}', bus='A')
    bus_B = FCpt(ICTBus, '{self.prefix}', bus='B')
    ch_1A = FCpt(ICTChannel, '{self.prefix}', channel='1A')
    ch_2A = FCpt(ICTChannel, '{self.prefix}', channel='2A')
    ch_3A = FCpt(ICTChannel, '{self.prefix}', channel='3A')
    ch_4A = FCpt(ICTChannel, '{self.prefix}', channel='4A')
    ch_5A = FCpt(ICTChannel, '{self.prefix}', channel='5A')
    ch_6A = FCpt(ICTChannel, '{self.prefix}', channel='6A')
    ch_1B = FCpt(ICTChannel, '{self.prefix}', channel='1B')
    ch_2B = FCpt(ICTChannel, '{self.prefix}', channel='2B')
    ch_3B = FCpt(ICTChannel, '{self.prefix}', channel='3B')
    ch_4B = FCpt(ICTChannel, '{self.prefix}', channel='4B')
    ch_5B = FCpt(ICTChannel, '{self.prefix}', channel='5B')
    ch_6B = FCpt(ICTChannel, '{self.prefix}', channel='6B')

    tab_component_names = True

    def __init__(self, prefix, name='ICT', **kwargs):
        self.prefix = prefix
        super().__init__(prefix, name=name, **kwargs)
