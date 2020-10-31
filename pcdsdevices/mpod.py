import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class MPODChannel(BaseInterface, Device):
    """
    MPOD Channel Object.

    Parameters
    ----------
    prefix : str
        The EPICS base of the MPOD Channel.

    name : str
        A name to refer to the device.
    """
    # TODO - might have too many Signals here!!
    voltage = Cpt(EpicsSignal, ':GetVoltageMeasurement',
                  write_pv=':SetVoltage', kind='normal',
                  doc='MPOD Channel Voltage Measurement [V]')
    max_voltage = Cpt(EpicsSignalRO, ':GetMaxVoltage', kind='normal',
                      doc='MPOD Channel Maximum Voltage [V]')
    terminal_voltage = Cpt(EpicsSignalRO, ':GetTerminalVoltageMeasurement',
                           kind='normal', doc='MPOD Terminal Voltage [V]')
    current = Cpt(EpicsSignalRO, ':GetCurrentMeasurement', kind='normal',
                  doc='MPOD Channel Current Measurement [A]')
    max_current = Cpt(EpicsSignalRO, ':GetMaxCurrent', kind='normal',
                      doc='MPOD Channel Max Current [A]')
    temperature = Cpt(EpicsSignalRO, ':GetTemperature', kind='normal',
                      doc='MPOD Temperature [C]')
    status_string = Cpt(EpicsSignalRO, ':GetStatusString',
                        kind='normal', doc='MPOD Channel Status String')
    # TODO - should i make this string=True?
    state = Cpt(EpicsSignal, ':GetSwitch', write_pv=':SetSwitch',
                kind='normal', doc='MPOD Channel State [Off/On]')
    # 0 means no EPICS high limit.
    voltage_high_limit = Cpt(EpicsSignal, ':SetVoltage.DRVH', kind='normal')

    tab_component_names = True
    tab_whitelist = ['on', 'off', 'set_voltage']

    def __init__(self, prefix, name='MPOD', **kwargs):
        super().__init__(prefix, name=name, **kwargs)

    def on(self):
        """Set mpod channel On"""
        self.state.put(1)

    def off(self):
        """Set mpod channel Off"""
        self.state.put(0)

    def set_voltage(self, voltage):
        """
        Set mpod channel voltage in V.

        Parameters
        ----------
        voltage : number
            Voltage in V.
        """
        self.voltage.put(voltage)


class MPODChannelHV(MPODChannel):
    """
    MPOD High Voltage Channel Object.

    Parameters
    ----------
    prefix: str
    The EPICS base of the MPOD Channel.

    name: str
    A name to refer to the device.
    """
    voltage_rise_rate = Cpt(EpicsSignal, ':GetVoltageRiseRate',
                            write_pv=':SetVoltageRiseRate', kind='normal',
                            doc='MPOD Channel Voltage Rise Rate [V/sec]')
    voltage_fall_rate = Cpt(EpicsSignal, ':GetVoltageFallRate',
                            write_pv=':SetVoltageFallRate', kind='normal',
                            doc='MPOD Channel Set Voltage Fall Rate [V/sec]')


class MPODChannelLV(MPODChannel):
    """
    MPOD Low Voltage Channel Object.

    TODO - might not need this here - might just use MPODChannel?

    Parameters
    ----------
    prefix: str
    The EPICS base of the MPOD Channel.

    name: str
    A name to refer to the device.
    """
    pass
