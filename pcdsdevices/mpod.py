import logging

from ophyd import FormattedComponent as FCpt
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
    channel_prefix : str
        The EPICS base of the MPOD Channel. E.g.: `XPP:R39:MPD:CH:0`
    card_prefix : str, optional
        The EPICS base of the MPOD Module. `XPP:R39:MPD:MOD:10`

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
        """Set the EmerOff state."""
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

    def set_voltage_rise_rate(self, rise_rate):
        """
        Set the voltage rise rate in V/sec.

        For the Low Voltage channels, it sets the voltage rise rate for each
        channel. For the High Voltage channels, it sets the voltage rise
        rate for the entire card.

        Parameters
        ----------
        rise_rate : number
            Voltage rise rate [V/sec].
        """
        self.voltage_rise_rate.put(rise_rate)

    def set_voltage_fall_rate(self, fall_rate):
        """
        Set the voltage fall rate in V/sec.

        For the Low Voltage channels, it sets the voltage fall rate for each
        channel. For the High Voltage channels, it sets the voltage fall
        rate for the entire card.

        Parameters
        ----------
        fall_rate : number
            Voltage fall rate [V/sec].
        """
        self.voltage_fall_rate.put(fall_rate)

    def get_max_voltage(self):
        return self.max_voltage.get()


class MPODChannelLV(MPODChannel):
    """
    MPOD Low Voltage Channel Object.

    Parameters
    ----------
    channel_prefix : str
        The EPICS base of the MPOD Channel. E.g.: `XPP:R39:MPD:CH:0`
    card_prefix : None
        The EPICS base of the MPOD HV Module.
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


class MPODChannelHV(MPODChannel):
    """
    MPOD High Voltage Channel Object.

    Parameters
    ----------
    channel_prefix : str
        The EPICS base of the MPOD Channel. E.g.: `XPP:R39:MPD:CH:100`
    card_prefix : str
        The EPICS base of the MPOD HV Module. E.g.: `XPP:R39:MPD:MOD:10`

    name: str
    A name to refer to the device.
    """
    tab_component_names = True
    tab_whitelist = ['set_voltage_rise_rate', 'set_voltage_fall_rate']

    voltage_rise_rate = FCpt(EpicsSignal, '{self._card_prefix}' +
                             ':GetVoltageRiseRate', kind='normal',
                             write_pv='{self._card_prefix}:SetVoltageRiseRate',
                             doc='MPOD Channel Voltage Rise Rate [V/sec]')
    voltage_fall_rate = FCpt(EpicsSignal, '{self._card_prefix}' +
                             ':GetVoltageFallRate', kind='normal',
                             write_pv='{self._card_prefix}:SetVoltageFallRate',
                             doc='MPOD Channel Set Voltage Fall Rate [V/sec]')

    def __init__(self, channel_prefix, card_prefix, name='mpod_hv_channel',
                 **kwargs):
        self._card_prefix = card_prefix
        super().__init__(channel_prefix, name=name, **kwargs)


def MPOD(channel_prefix, card_prefix=None, **kwargs):
    """
    Determine the appropriate MPOD Channel class based on the max voltage.

    Usign 50V as line between the HV and LV max voltage settings.

    Parameters
    ----------
    channel_prefix : str
        Epics base PV for channels.
    card_prefix : str
        Epics base PV for the whole MPOD module, HV Channels.
    kwargs : dict
        Information to pass through to the device, upon initialization
    """
    mpod = MPODChannel(channel_prefix)
    try:
        voltage = mpod.get_max_voltage()
    except Exception:
        return None
    else:
        if voltage < 50:
            return MPODChannelLV(channel_prefix, **kwargs)
        try:
            base, channel = channel_prefix.split('CH:')
        except Exception:
            return None
        else:
            card_number = get_card_number(channel)
            card = f'{base}MOD:{card_number}'
            return MPODChannelHV(channel_prefix, card, **kwargs)


def get_card_number(channel):
    """
    Helper for creating the card prefix for HV channels.

    For channels `[0-7]` - it will return None
    For channels `[000-015] - it will return `0`
    For channels `[100-107] - it will return `10`
    FOr channels `[200-207] - it will return `20`
    and so on...

    Parameters
    ----------
    channel : str

    Returns
    -------
    channel : number or None
        Number to use for the MPOD card.
    """
    if len(channel) <= 1:
        return None
    else:
        channel = int(channel)
        while channel >= 10:
            channel /= 10
        if channel == 0:
            return channel
        return (int(channel) * 10)


class CxiMPODD50(MPODChannelLV, MPODChannelHV):
    """
    IOC = CXI:IOC:MPOD:D51

    CXI:D51:MPD:CH:[200-207] LV
    CXI:D51:MPD:CH:[100-107] LV
    CXI:D51:MPD:CH:[0-7] HV

    caget CXI:D51:MPD:CH:200:GetMaxVoltage 8
    caget CXI:D51:MPD:CH:100:GetMaxVoltage 8
    caget CXI:D51:MPD:CH:0:GetMaxVoltage 1000
    """
    pass


class CxiMPODD51(MPODChannelLV, MPODChannelHV):
    """
    IOC = CXI:IOC:MPOD:D51

    CXI:D51:MPD:CH:[200-207] LV
    CXI:D51:MPD:CH:[100-107] LV
    CXI:D51:MPD:CH:[0-7] HV

    caget CXI:D51:MPD:CH:200:GetMaxVoltage 8
    caget CXI:D51:MPD:CH:100:GetMaxVoltage 8
    caget CXI:D51:MPD:CH:0:GetMaxVoltage 1000
    """
    pass


class DetMbl02MPOD(MPODChannelLV, MPODChannelHV):
    """
    IOC = DET:IOC:DET:MPOD:2

    DET:MBL2:MPD:CH:[0-7] HV
    DET:MBL2:MPD:CH:[100-107] LV
    DET:MBL2:MPD:CH:[200-207] LV

    caget DET:MBL2:MPD:CH:0:GetMaxVoltage 1000
    caget DET:MBL2:MPD:CH:100:GetMaxVoltage 8
    caget DET:MBL2:MPD:CH:200:GetMaxVoltage 8
    """
    pass


class MecMPODD60(MPODChannelLV, MPODChannelHV):
    """
    IOC = IOC:MEC:MPOD:D60

    MEC:D60:MPD:CH:[200-207] LV
    MEC:D60:MPD:CH:[100-107] LV
    MEC:D60:MPD:CH:[0-7] HV

    caget MEC:D60:MPD:CH:200:GetMaxVoltage 8
    caget MEC:D60:MPD:CH:100:GetMaxVoltage 8
    caget MEC:D60:MPD:CH:0:GetMaxVoltage 1000
    """


class MfxDetMPOD(MPODChannelLV, MPODChannelHV):
    """
    MFX:DET:MPD:CH:[000-015] HV
    MFX:DET:MPD:CH:[100-107] LV
    MFX:DET:MPD:CH:[200-207] LV
    MFX:DET:MPD:CH:[300-307] LV

    caget MFX:DET:MPD:CH:000:GetMaxVoltage 1000

    caget MFX:DET:MPD:CH:100:GetMaxVoltage 8
    caget MFX:DET:MPD:CH:200:GetMaxVoltage 8
    caget MFX:DET:MPD:CH:300:GetMaxVoltage 8
    """
    pass


class XppMPOD(MPODChannelLV, MPODChannelHV):
    """
    IOC = XPP:IOC:MPOD

    XPP:DET:MPD:CH:[0-7] LV
    XPP:DET:MPD:CH:[100-107] LV
    XPP:DET:MPD:CH:[200-207] HV

    caget XPP:DET:MPD:CH:0:GetMaxVoltage 8
    caget XPP:DET:MPD:CH:100:GetMaxVoltage 8
    caget XPP:DET:MPD:CH:200:GetMaxVoltage 1000
    """
    pass


class XppUsrMPOD(MPODChannelLV, MPODChannelHV):
    """
    IOC = XPP:IOC:USR:MPOD

    XPP:R39:MPD:CH:[0-7] LV
    XPP:R39:MPD:CH:[100-107] HV
    XPP:R39:MPD:CH:[200-207] HV
    XPP:R39:MPD:CH:[300-307] LV

    caget XPP:R39:MPD:CH:0:GetMaxVoltage 30
    caget XPP:R39:MPD:CH:100:GetMaxVoltage 6000
    caget XPP:R39:MPD:CH:200:GetMaxVoltage 500
    caget XPP:R39:MPD:CH:300:GetMaxVoltage 8
    """
    pass
