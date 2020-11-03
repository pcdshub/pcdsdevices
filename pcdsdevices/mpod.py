import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd import FormattedComponent as FCpt
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
    voltage = Cpt(EpicsSignal, ':GetVoltageMeasurement',
                  write_pv=':SetVoltage', kind='normal',
                  doc='MPOD Channel Voltage Measurement [V]')
    max_voltage = Cpt(EpicsSignalRO, ':GetMaxVoltage', kind='normal',
                      doc='MPOD Channel Maximum Voltage [V]')
    terminal_voltage = Cpt(EpicsSignalRO, ':GetTerminalVoltageMeasurement',
                           kind='normal', doc='MPOD Terminal Voltage [V]')
    current = Cpt(EpicsSignal, ':GetCurrentMeasurement',
                  write_pv=':SetCurrent', kind='normal',
                  doc='MPOD Channel Current Measurement [A]')
    max_current = Cpt(EpicsSignalRO, ':GetMaxCurrent', kind='normal',
                      doc='MPOD Channel Max Current [A]')
    temperature = Cpt(EpicsSignalRO, ':GetTemperature', kind='normal',
                      doc='MPOD Temperature [C]')
    status_string = Cpt(EpicsSignalRO, ':GetStatusString',
                        kind='normal', doc='MPOD Channel Status String')
    state = Cpt(EpicsSignal, ':GetSwitch', write_pv=':SetSwitch',
                kind='normal', string=True,
                doc='MPOD Channel State [Off/On/Reset/EmerOff/ClrEvnt]')
    # 0 means no EPICS high limit.
    voltage_high_limit = Cpt(EpicsSignal, ':SetVoltage.DRVH', kind='normal')

    tab_component_names = True
    tab_whitelist = ['on', 'off', 'reset', 'emer_off', 'clr_evnt',
                     'set_voltage', 'set_current']

    def __init__(self, channel_prefix, card_prefix=None, name='MPOD',
                 **kwargs):
        super().__init__(channel_prefix, name=name, **kwargs)

    def on(self):
        """Set mpod channel On."""
        self.state.put('On')

    def off(self):
        """Set mpod channel Off."""
        self.state.put('Off')

    def reset(self):
        """Reset mpod channel."""
        self.state.put('Reset')

    def emer_off(self):
        """TODO: find out what this is."""
        self.state.put('EmerOff')

    def clr_evnt(self):
        """Clear Event."""
        self.state.put('ClrEvnt')

    def set_voltage(self, voltage):
        """
        Set mpod channel voltage in V.

        Parameters
        ----------
        voltage : number
            Voltage in V.
        """
        self.voltage.put(voltage)

    def set_current(self, current):
        """
        Set mpod channel current in A.

        Parameters
        ----------
        current : number
            Current in A.
        """
        self.current.put(current)


class LVChannel(MPODChannel):
    """
    MPOD Low Voltage Channel Object.

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

    tab_component_names = True
    tab_whitelist = ['set_voltage_rise_rate', 'set_voltage_fall_rate']

    def set_voltage_rise_rate(self, rise_rate):
        """
        Set the mpod channel voltage rise rate in V/sec.

        Parameters
        ----------
        rise_rate : number
            Voltage rise rate [V/sec].
        """
        self.voltage_rise_rate.put(rise_rate)

    def set_voltage_fall_rate(self, fall_rate):
        """
        Set the mpod channel voltage fall rate in V/sec.

        Parameters
        ----------
        fall_rate : number
            Voltage fall rate [V/sec].
        """
        self.voltage_fall_rate.put(fall_rate)


class HVChannel(MPODChannel):
    """
    MPOD High Voltage Channel Object.

    Parameters
    ----------
    prefix: str
    The EPICS base of the MPOD Channel. E.g.: `XPP:R39:MPD`

    name: str
    A name to refer to the device.
    """
    tab_component_names = True
    tab_whitelist = ['set_voltage_rise_rate', 'set_voltage_fall_rate']

    voltage_rise_rate = FCpt(EpicsSignal, '{self._card_prefix}' +
                             ':GetVoltageRiseRate',
                             write_pv=':SetVoltageRiseRate', kind='normal',
                             doc='MPOD Channel Voltage Rise Rate [V/sec]')
    voltage_fall_rate = FCpt(EpicsSignal, '{self._card_prefix}' +
                             ':GetVoltageFallRate',
                             write_pv=':SetVoltageFallRate', kind='normal',
                             doc='MPOD Channel Set Voltage Fall Rate [V/sec]')

    def set_voltage_rise_rate(self, rise_rate):
        """
        Set the MPOD module voltage rise rate in V/sec.

        Parameters
        ----------
        rise_rate : number
            Voltage rise rate [V/sec].
        """
        self.voltage_rise_rate.put(rise_rate)

    def set_voltage_fall_rate(self, fall_rate):
        """
        Set the MPOD module voltage fall rate in V/sec.

        Parameters
        ----------
        fall_rate : number
            Voltage fall rate [V/sec].
        """
        self.voltage_fall_rate.put(fall_rate)

    def __init__(self, channel_prefix, card_prefix, name='hv_mpod', **kwargs):
        self._card_prefix = card_prefix
        super().__init__(channel_prefix, name=name, **kwargs)
