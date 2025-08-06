"""
Standard classes for L2SI DC power devices.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

logger = logging.getLogger(__name__)


class PDUChannel(Device):
    """
    Class to define a particular channel of the PDU.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant PDU.

    channel : str
        The output channel on the PDU, e.g. '1', '2', etc.
    """

    ch_index = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_index}', kind='hinted', string=True)
    ch_name = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_name}', kind='hinted', string=True)
    ch_status = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_status}', kind='hinted', string=True)
    ch_ctrl_state = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_ctrl_state}', kind='hinted', string=True)
    ch_ctrl_command_on = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_on}', kind='omitted', string=True)
    ch_ctrl_command_off = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_off}', kind='omitted', string=True)
    ch_ctrl_command_reboot = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_reboot}', kind='omitted', string=True)

    def __init__(self, prefix, *, name=None, parent=None, channel=None, **kwargs):
        self._ch = f'{channel}'
        self._ch_index = 'GetID'
        self._ch_status = 'GetStatus'
        self._ch_name = 'SetName'
        self._ch_ctrl_state = 'GetControlState'
        self._ch_command_on = 'TurnOn'
        self._ch_command_off = 'TurnOff'
        self._ch_command_reboot = 'CycleOffOn'

        super().__init__(prefix, name=name, **kwargs)


class TripplitePDUChannel(Device):
    """
    Class to define a particular channel of a Tripplite PDU.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant PDU.

    channel : str
        The output channel on the PDU, e.g. '1', '2', etc.

    """
    ch_index = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_index}', kind='hinted', string=True)
    ch_name = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_name}', kind='hinted', string=True)
    ch_status = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_status}', kind='hinted', string=True)
    ch_ctrl_state = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_ctrl_state}', kind='hinted', string=True)
    ch_ctrl_command = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command}', kind='hinted', string=True)

    def __init__(self, prefix, *, name=None, parent=None, channel=None, **kwargs):
        self._ch = f'{channel}'
        self._ch_index = 'getPduOutletIndex'
        self._ch_status = 'getPduOutletState'
        self._ch_name = 'setPduOutletName'
        self._ch_ctrl_state = 'getPduOutletControllable'
        self._ch_command = 'setPduOutletCommand'

        super().__init__(prefix, name=name, **kwargs)


class PDU(Device):
    """
    Class to define a non-Tripplite PDU

    Parameters
    ---------
    prefix : str
        The base PV of the relevant PDU.

    num_channels : int
        The output channels for the PDU.

    pdu_type : str
        The pdu type, e.g Leviton, or Sentry4
    """

    tower_name = FCpt(EpicsSignal, '{prefix}{self._tower}:SetTowerName', kind='hinted')
    location = Cpt(EpicsSignal, ':SetSystemLocation', kind='hinted')
    status = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetTowerStatus', kind='hinted')
    output_c_max = FCpt(EpicsSignal, '{prefix}{self._tower}:SetInfeedLoadHighThresh', kind='hinted')
    output_c = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetInfeedLoadValue', kind='hinted')
    output_c_status = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetInfeedLoadStatus', kind='hinted')
    output_p = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetTowerActivePower', kind='hinted')

    temperature_lo = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetTempLowThresh', kind='hinted')
    humidity_lo = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetHumidLowThresh', kind='hinted')
    temperature_hi = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetTempHighThresh', kind='hinted')
    humidity_hi = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetHumidHighThresh', kind='hinted')

    sensor1_id = Cpt(EpicsSignal, ':Sensor:1:GetID', kind='hinted')
    sensor1_status = Cpt(EpicsSignal, ':Sensor:1:GetStatus', kind='hinted')
    sensor1_temperature = Cpt(EpicsSignal, ':Sensor:1:GetTempStatus', kind='hinted')
    sensor1_humidity = Cpt(EpicsSignal, ':Sensor:1:GetHumidStatus', kind='hinted')

    sensor2_id = Cpt(EpicsSignal, ':Sensor:2:GetID', kind='hinted')
    sensor2_status = Cpt(EpicsSignal, ':Sensor:2:GetStatus', kind='hinted')
    sensor2_temperature = Cpt(EpicsSignal, ':Sensor:2:GetTempStatus', kind='hinted')
    sensor2_humidity = Cpt(EpicsSignal, ':Sensor:2:GetHumidStatus', kind='hinted')

    channel_ctrl = FCpt(EpicsSignal, '{prefix}{self._ctrl}:SetControlAction', kind='hinted')

    tab_component_names = True

    def __init__(self, prefix, num_channels, pdu_type=None, name=None, **kwargs):

        if pdu_type.lower() == 'sentry4':
            self._tower = ":1"
            if num_channels == 8:
                self._ctrl = ":Outlet:G1"
            else:
                self._ctrl = ":Outlet:All"
        else:
            self._tower = ":"
            self._ctrl = ":Outlet:All"

        self.num_channels = num_channels

        super().__init__(prefix, name=name, **kwargs)


class PDU8(PDU):
    """8-channel PDU with static channel definitions for Typhos"""

    channel1 = Cpt(PDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(PDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(PDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(PDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(PDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(PDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(PDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(PDUChannel, '', channel=8, kind='normal')

    def __init__(self, prefix, pdu_type=None, name=None, **kwargs):
        super().__init__(prefix, num_channels=8, pdu_type=pdu_type, name=name, **kwargs)


class PDU16(PDU):
    """16-channel PDU with static channel definitions for Typhos"""

    channel1 = Cpt(PDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(PDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(PDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(PDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(PDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(PDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(PDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(PDUChannel, '', channel=8, kind='normal')
    channel9 = Cpt(PDUChannel, '', channel=9, kind='normal')
    channel10 = Cpt(PDUChannel, '', channel=10, kind='normal')
    channel11 = Cpt(PDUChannel, '', channel=11, kind='normal')
    channel12 = Cpt(PDUChannel, '', channel=12, kind='normal')
    channel13 = Cpt(PDUChannel, '', channel=13, kind='normal')
    channel14 = Cpt(PDUChannel, '', channel=14, kind='normal')
    channel15 = Cpt(PDUChannel, '', channel=15, kind='normal')
    channel16 = Cpt(PDUChannel, '', channel=16, kind='normal')

    def __init__(self, prefix, pdu_type=None, name=None, **kwargs):
        super().__init__(prefix, num_channels=16, pdu_type=pdu_type, name=name, **kwargs)


class PDU24(PDU):
    """24-channel PDU with static channel definitions for Typhos"""

    channel1 = Cpt(PDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(PDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(PDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(PDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(PDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(PDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(PDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(PDUChannel, '', channel=8, kind='normal')
    channel9 = Cpt(PDUChannel, '', channel=9, kind='normal')
    channel10 = Cpt(PDUChannel, '', channel=10, kind='normal')
    channel11 = Cpt(PDUChannel, '', channel=11, kind='normal')
    channel12 = Cpt(PDUChannel, '', channel=12, kind='normal')
    channel13 = Cpt(PDUChannel, '', channel=13, kind='normal')
    channel14 = Cpt(PDUChannel, '', channel=14, kind='normal')
    channel15 = Cpt(PDUChannel, '', channel=15, kind='normal')
    channel16 = Cpt(PDUChannel, '', channel=16, kind='normal')
    channel17 = Cpt(PDUChannel, '', channel=17, kind='normal')
    channel18 = Cpt(PDUChannel, '', channel=18, kind='normal')
    channel19 = Cpt(PDUChannel, '', channel=19, kind='normal')
    channel20 = Cpt(PDUChannel, '', channel=20, kind='normal')
    channel21 = Cpt(PDUChannel, '', channel=21, kind='normal')
    channel22 = Cpt(PDUChannel, '', channel=22, kind='normal')
    channel23 = Cpt(PDUChannel, '', channel=23, kind='normal')
    channel24 = Cpt(PDUChannel, '', channel=24, kind='normal')

    def __init__(self, prefix, pdu_type=None, name=None, **kwargs):
        super().__init__(prefix, num_channels=24, pdu_type=pdu_type, name=name, **kwargs)


class TripplitePDU(Device):
    """
        Class to define a Tripplite PDU.

        Parameters
        ---------
        prefix : str
            The base PV of the relevant PDU.

        num_channels : int
            The output channels for the PDU.
    """

    tower_name = Cpt(EpicsSignal, ':setDeviceName', kind='hinted')
    location = Cpt(EpicsSignal, ':setDeviceLocation', kind='hinted')
    status = Cpt(EpicsSignalRO, ':getDeviceStatus', kind='hinted')

    num_inputs = Cpt(EpicsSignalRO, ':getPduIdentNumInputs', kind='hinted')
    num_outputs = Cpt(EpicsSignalRO, ':getPduIdentNumOutputs', kind='hinted')
    num_outlets = Cpt(EpicsSignalRO, ':getPduIdentNumOutlets', kind='hinted')
    num_groups = Cpt(EpicsSignalRO, ':getPduIdentNumOutletGroups', kind='hinted')
    num_phases = Cpt(EpicsSignalRO, ':getPduIdentNumPhases', kind='hinted')
    num_circuits = Cpt(EpicsSignalRO, ':getPduIdentNumCircuits', kind='hinted')
    num_breakers = Cpt(EpicsSignalRO, ':getPduIdentNumBreakers', kind='hinted')
    num_heatsinks = Cpt(EpicsSignalRO, ':getPduIdentNumHeatsinks', kind='hinted')

    input_f = Cpt(EpicsSignalRO, ':getPduInputPhaseFrequency', kind='hinted')

    input_v = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltage', kind='hinted')
    input_v_min = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltageMin', kind='hinted')
    input_v_max = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltageMax', kind='hinted')

    output_f = Cpt(EpicsSignalRO, ':getPduOutputFrequency', kind='hinted')
    output_v = Cpt(EpicsSignalRO, ':getPduOutputVoltage', kind='hinted')
    output_p = Cpt(EpicsSignalRO, ':getPduOutputActivePower', kind='hinted')
    output_c = Cpt(EpicsSignalRO, ':getPduOutputCurrent', kind='hinted')
    output_c_min = Cpt(EpicsSignalRO, ':getPduOutputCurrentMin', kind='hinted')
    output_c_max = Cpt(EpicsSignalRO, ':getPduOutputCurrentMax', kind='hinted')

    channels_on = Cpt(EpicsSignal, ':setPduControlPduOn', kind='hinted')
    channels_off = Cpt(EpicsSignal, ':setPduControlPduOff', kind='hinted')
    channels_reboot = Cpt(EpicsSignal, ':setPduControlPduReboot', kind='hinted')

    tab_component_names = True

    def __init__(self, prefix, num_channels, name=None, **kwargs):

        self.num_channels = num_channels

        super().__init__(prefix, name=name, **kwargs)


class TripplitePDU8(TripplitePDU):
    """8-channel Tripplite PDU with static channel definitions for Typhos"""

    channel1 = Cpt(TripplitePDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(TripplitePDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(TripplitePDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(TripplitePDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(TripplitePDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(TripplitePDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(TripplitePDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(TripplitePDUChannel, '', channel=8, kind='normal')

    def __init__(self, prefix, name=None, **kwargs):
        super().__init__(prefix, num_channels=8, name=name, **kwargs)


class TripplitePDU16(TripplitePDU):
    """16-channel Tripplite PDU with static channel definitions for Typhos"""

    channel1 = Cpt(TripplitePDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(TripplitePDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(TripplitePDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(TripplitePDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(TripplitePDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(TripplitePDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(TripplitePDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(TripplitePDUChannel, '', channel=8, kind='normal')
    channel9 = Cpt(TripplitePDUChannel, '', channel=9, kind='normal')
    channel10 = Cpt(TripplitePDUChannel, '', channel=10, kind='normal')
    channel11 = Cpt(TripplitePDUChannel, '', channel=11, kind='normal')
    channel12 = Cpt(TripplitePDUChannel, '', channel=12, kind='normal')
    channel13 = Cpt(TripplitePDUChannel, '', channel=13, kind='normal')
    channel14 = Cpt(TripplitePDUChannel, '', channel=14, kind='normal')
    channel15 = Cpt(TripplitePDUChannel, '', channel=15, kind='normal')
    channel16 = Cpt(TripplitePDUChannel, '', channel=16, kind='normal')

    def __init__(self, prefix, name=None, **kwargs):
        super().__init__(prefix, num_channels=16, name=name, **kwargs)


class TripplitePDU24(TripplitePDU):
    """24-channel Tripplite PDU with static channel definitions for Typhos"""

    channel1 = Cpt(TripplitePDUChannel, '', channel=1, kind='normal')
    channel2 = Cpt(TripplitePDUChannel, '', channel=2, kind='normal')
    channel3 = Cpt(TripplitePDUChannel, '', channel=3, kind='normal')
    channel4 = Cpt(TripplitePDUChannel, '', channel=4, kind='normal')
    channel5 = Cpt(TripplitePDUChannel, '', channel=5, kind='normal')
    channel6 = Cpt(TripplitePDUChannel, '', channel=6, kind='normal')
    channel7 = Cpt(TripplitePDUChannel, '', channel=7, kind='normal')
    channel8 = Cpt(TripplitePDUChannel, '', channel=8, kind='normal')
    channel9 = Cpt(TripplitePDUChannel, '', channel=9, kind='normal')
    channel10 = Cpt(TripplitePDUChannel, '', channel=10, kind='normal')
    channel11 = Cpt(TripplitePDUChannel, '', channel=11, kind='normal')
    channel12 = Cpt(TripplitePDUChannel, '', channel=12, kind='normal')
    channel13 = Cpt(TripplitePDUChannel, '', channel=13, kind='normal')
    channel14 = Cpt(TripplitePDUChannel, '', channel=14, kind='normal')
    channel15 = Cpt(TripplitePDUChannel, '', channel=15, kind='normal')
    channel16 = Cpt(TripplitePDUChannel, '', channel=16, kind='normal')
    channel17 = Cpt(TripplitePDUChannel, '', channel=17, kind='normal')
    channel18 = Cpt(TripplitePDUChannel, '', channel=18, kind='normal')
    channel19 = Cpt(TripplitePDUChannel, '', channel=19, kind='normal')
    channel20 = Cpt(TripplitePDUChannel, '', channel=20, kind='normal')
    channel21 = Cpt(TripplitePDUChannel, '', channel=21, kind='normal')
    channel22 = Cpt(TripplitePDUChannel, '', channel=22, kind='normal')
    channel23 = Cpt(TripplitePDUChannel, '', channel=23, kind='normal')
    channel24 = Cpt(TripplitePDUChannel, '', channel=24, kind='normal')

    def __init__(self, prefix, name=None, **kwargs):
        super().__init__(prefix, num_channels=24, name=name, **kwargs)
