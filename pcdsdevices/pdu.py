"""
Standard classes for L2SI DC power devices.
"""
import logging

from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt
from ophyd import Component as Cpt

from .device import GroupDevice
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class PDUChannel(Device):
    """
    Class to define a particular channel of the PDU.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant PDU.

    channel : str
        The output channel on the pPDU, e.g. '1', '2', etc.

    pdu_type : str
        The pdu type, e.g TrippLite, Leviton, or Sentry
    """

    ch_index = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_index}',
                    kind='hinted', string=True)
    ch_name = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_name}',
                    kind='hinted', string=True)
    ch_status = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_status}',
                    kind='hinted', string=True)
    ch_ctrl_state = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_ctrl_state}',
                    kind='hinted', string=True)
    ch_ctrl_command_on = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_on}',
                    kind='hinted', string=True)
    ch_ctrl_command_off = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_off}',
                    kind='hinted', string=True)
    ch_ctrl_command_reboot = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command_reboot}',
                    kind='hinted', string=True)

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
        The output channel on the pPDU, e.g. '1', '2', etc.

    pdu_type : str
        The pdu type, e.g TrippLite, Leviton, or Sentry
    """
    ch_index = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_index}',
                    kind='hinted', string=True)
    ch_name = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_name}',
                    kind='hinted', string=True)
    ch_status = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_status}',
                    kind='hinted', string=True)
    ch_ctrl_state = FCpt(EpicsSignalRO, '{self.prefix}:Outlet:{self._ch}:{self._ch_ctrl_state}',
                    kind='hinted', string=True)
    ch_ctrl_command = FCpt(EpicsSignal, '{self.prefix}:Outlet:{self._ch}:{self._ch_command}',
                    kind='hinted', string=True)

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
    Class to define a non-Tripplite PDU.

    Parameters
    ---------
    prefix : str
        The base PV of the relevant PDU.

    num_channels : int
        The output channels for the PDU.

    """

    pdu_name = FCpt(EpicsSignal, '{prefix}{self._tower}:SetTowerName', kind='hinted')
    pdu_location = Cpt(EpicsSignal, ':SetSystemLocation', kind='hinted')
    pdu_status = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetTowerStatus', kind='hinted')
    pdu_output_c_max = FCpt(EpicsSignalRO, '{prefix}{self._tower}:SetInfeedLoadHighThresh', kind='hinted')
    pdu_output_c = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetInfeedLoadValue', kind='hinted')
    pdu_output_c_status = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetInfeedLoadStatus', kind='hinted')
    pdu_output_p = FCpt(EpicsSignalRO, '{prefix}{self._tower}:GetTowerActivePower', kind='hinted')


    pdu_temperature_lo = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetTempLowThresh', kind='hinted')
    pdu_humidity_lo = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetHumidLowThresh', kind='hinted')
    pdu_temperature_hi = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetTempHighThresh', kind='hinted')
    pdu_humidity_hi = FCpt(EpicsSignal, '{prefix}{self._tower}:Sensor:All:SetHumidHighThresh', kind='hinted')

    pdu_sensor1_id = Cpt(EpicsSignal, ':Sensor:1:GetID', kind='hinted')
    pdu_sensor1_status = Cpt(EpicsSignal, ':Sensor:1:GetStatus', kind='hinted')
    pdu_sensor1_temperature = Cpt(EpicsSignal, ':Sensor:1:GetTempStatus', kind='hinted')
    pdu_sensor1_humidity = Cpt(EpicsSignal, ':Sensor:1:GetHumidStatus', kind='hinted')

    pdu_sensor2_id = Cpt(EpicsSignal, ':Sensor:2:GetID', kind='hinted')
    pdu_sensor2_status = Cpt(EpicsSignal, ':Sensor:2:GetStatus', kind='hinted')
    pdu_sensor2_temperature = Cpt(EpicsSignal, ':Sensor:2:GetTempStatus', kind='hinted')
    pdu_sensor2_humidity = Cpt(EpicsSignal, ':Sensor:2:GetHumidStatus', kind='hinted')

    channel_ctrl = FCpt(EpicsSignal, '{prefix}{self._ctrl}:SetControlAction', kind='hinted')


    tab_component_names = True

    def __init__(self, prefix, num_channels, pdu_type=None, name='PDU', **kwargs):

        if pdu_type.lower() == 'sentry4':
            self._tower = ":1"
            self._ctrl = ":Outlet:G1"
        else:
            self._tower = ":"
            self._ctrl = ":Outlet:All"

        # Dynamically create channels here
        for i in range(1, num_channels + 1):
            ch = PDUChannel(f"{prefix}", name=f"channel{i}", channel=i)
            setattr(self, f'channel{i}', ch)

        self.num_channels = num_channels

        super().__init__(prefix, name=name, **kwargs)


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

    pdu_name = Cpt(EpicsSignal, ':setDeviceName', kind='hinted')
    pdu_location = Cpt(EpicsSignal, ':setDeviceLocation', kind='hinted')
    pdu_status = Cpt(EpicsSignalRO, ':getDeviceStatus', kind='hinted')

    pdu_num_inputs = Cpt(EpicsSignalRO, ':getPduIdentNumInputs', kind='hinted')
    pdu_num_outputs = Cpt(EpicsSignalRO, ':getPduIdentNumOutputs', kind='hinted')
    pdu_num_outlets = Cpt(EpicsSignalRO, ':getPduIdentNumOutlets', kind='hinted')
    pdu_num_groups = Cpt(EpicsSignalRO, ':getPduIdentNumOutletGroups', kind='hinted')
    pdu_num_phases = Cpt(EpicsSignalRO, ':getPduIdentNumPhases', kind='hinted')
    pdu_num_circuits = Cpt(EpicsSignalRO, ':getPduIdentNumCircuits', kind='hinted')
    pdu_num_breakers = Cpt(EpicsSignalRO, ':getPduIdentNumBreakers', kind='hinted')
    pdu_num_heatsinks = Cpt(EpicsSignalRO, ':getPduIdentNumHeatsinks', kind='hinted')

    pdu_input_f = Cpt(EpicsSignalRO, ':getPduInputPhaseFrequency', kind='hinted')

    pdu_input_v = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltage', kind='hinted')
    pdu_input_v_min = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltageMin', kind='hinted')
    pdu_input_v_max = Cpt(EpicsSignalRO, ':getPduInputPhaseVoltageMax', kind='hinted')

    pdu_output_f = Cpt(EpicsSignalRO, ':getPduOutputFrequency', kind='hinted')
    pdu_output_v = Cpt(EpicsSignalRO, ':getPduOutputVoltage', kind='hinted')
    pdu_output_p = Cpt(EpicsSignalRO, ':getPduOutputActivePower', kind='hinted')
    pdu_output_c = Cpt(EpicsSignalRO, ':getPduOutputCurrent', kind='hinted')
    pdu_output_c_min = Cpt(EpicsSignalRO, ':getPduOutputCurrentMin', kind='hinted')
    pdu_output_c_max = Cpt(EpicsSignalRO, ':getPduOutputCurrentMax', kind='hinted')

    channels_on = Cpt(EpicsSignal, ':setPduControlPduOn', kind='hinted')
    channels_off = Cpt(EpicsSignal, ':setPduControlPduOff', kind='hinted')
    channels_reboot = Cpt(EpicsSignal, ':setPduControlPduReboot', kind='hinted')

    tab_component_names = True

    def __init__(self, prefix, num_channels, name='PDU', **kwargs):

        # Dynamically create channels here
        for i in range(1, num_channels + 1):
            ch = TripplitePDUChannel(f"{prefix}", name=f"channel{i}", channel=i)
            setattr(self, f'channel{i}', ch)

        self.num_channels = num_channels

        super().__init__(prefix, name=name, **kwargs)
