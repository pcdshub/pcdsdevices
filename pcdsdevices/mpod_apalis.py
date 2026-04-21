import logging
import time

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface
from pcdsdevices.signal import EpicsSignalEditMD

from .device import GroupDevice

logger = logging.getLogger(__name__)


class MPODApalisChannel(BaseInterface, Device):
    """
    MPODApalis Channel Object.  Takes voltage limit from the parent module,
    and as such MUST only be used as a Component of MPODApalisModule for limits
    to make sense

    Parameters
    ----------
    prefix : str
        The EPICS base of the MPOD Channel, e.g. 'TMO:MPOD:01:M6:C6'.
    name : str, keyword-only
        A name to refer to the device.
    """
    voltage = Cpt(
        EpicsSignalEditMD, ':VoltageMeasure',
        write_pv=':VoltageSet', kind='normal', limits=True,
        doc=(
            "MPOD Channel Voltage Measurement [V]. "
            "The value of this signal is the actual measured voltage "
            "of the channel. If you put to this signal it will change "
            "the channel's voltage setpoint."
        ),
    )

    max_voltage = Cpt(EpicsSignalRO, ':VoltageNominal', kind='normal',
                      doc='MPOD Channel Maximum Voltage [V]')

    current = Cpt(
        EpicsSignalEditMD, ':CurrentMeasure',
        write_pv=':CurrentSet', kind='normal', limits=True,
        doc=(
            "MPOD Channel Current Measurement [A]. "
            "The value of this signal is the actual measured current "
            "of the channel. If you put to this signal it will change "
            "the channel's current setpoint."
        ),
    )

    max_current = Cpt(EpicsSignalRO, ':CurrentNominal', kind='normal',
                      doc='MPOD Channel Current Maximum')

    state = Cpt(EpicsSignal, ':isOn', write_pv=':Control:setOn',
                kind='normal', string=True,
                doc='MPOD Channel State [Off/On]')

    desc = Cpt(EpicsSignal, ':VoltageMeasure.DESC', kind='normal',
               doc='MPOD Channel Description')

    last_voltage_set = Cpt(
        EpicsSignalRO, ':VoltageSet', kind='normal',
        doc=(
            'Readback to verify the MPOD Channel Voltage Setpoint [V]. '
            'This is used to compare the measured readback voltage with '
            'the last value we set to the channel. '
            'To change the voltage, use the voltage signal or the '
            'set_voltage helper method.'
        )
    )

    is_trip = Cpt(EpicsSignalRO, ':isTrip', kind='omitted',
                  doc='True if MPOD channel is tripped.')

    event_trip = Cpt(
        EpicsSignalRO, ':EventTrip', kind='normal',
        doc=(
            'Latching bit that event supply is not good.'
            'External supply exceeds lower or upper limits.'
        )
    )

    tab_component_names = True
    tab_whitelist = ['on', 'off',
                     'set_voltage', 'set_current']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._max_voltage = 100

    @property
    def voltage_setpoint(self) -> EpicsSignalRO:
        """Name alias for backwards compatibility."""
        return self.last_voltage_set

    def on(self):
        """Set mpod channel On."""
        self.state.put(1)

    def off(self):
        """Set mpod channel Off."""
        self.state.put(0)

    def set_voltage(self, voltage_number: float) -> None:
        """
        Set mpod channel voltage in V.

        Values above or below the channel's range will be clamped
        to the range.

        Parameters
        ----------
        voltage_number : number
            Voltage in V.
        """
        return _put_clamped(signal=self.voltage, value=voltage_number)

    def set_current(self, current_number: float) -> None:
        """
        Set mpod channel current in A.

        Values above or below the channel's range will be clamped
        to the range.

        Parameters
        ----------
        current_number : number
            Current in A.
        """
        return _put_clamped(signal=self.current, value=current_number)

    @max_voltage.sub_value
    def _new_max_voltage(self, value: float, **kwargs) -> None:
        self._max_voltage = value
        self._update_max_voltage_limits()

    def _update_max_voltage_limits(self) -> None:
        """
        Update limits on voltage, referring to the parent module if it exists

        If parent module does not exist, defaults limits to (0, 100)
        """
        limit_pct = getattr(self, "biological_parent.limit_percents", (0, 100))
        limits = [lim * self._max_voltage / 100 for lim in limit_pct]

        self.voltage._override_metadata(
            lower_ctrl_limit=min(limits),
            upper_ctrl_limit=max(limits),
        )

    @max_current.sub_value
    def _new_max_current(self, value: float, **kwargs) -> None:
        """Set explicit limits on current for better error reporting."""
        bounds = (0, value)
        self.current._override_metadata(
            lower_ctrl_limit=min(bounds),
            upper_ctrl_limit=max(bounds),
        )


def _put_clamped(signal: EpicsSignal, value: float) -> None:
    """
    Force put value to be within the limits of the signal.

    Warn if the value is outside the range and needed to be clamped
    """
    low_val = min(signal.limits)
    high_val = max(signal.limits)

    def local_warn(alt_value: float):
        logger.warning(
            "Cannot put %g. The limits are %s, will set %s to %g",
            value, signal.limits, signal.attr_name, alt_value,
        )

    if value < low_val:
        local_warn(alt_value=low_val)
        value = low_val
    elif value > high_val:
        local_warn(alt_value=high_val)
        value = high_val

    signal.put(value)


class MPODApalisModule(BaseInterface, GroupDevice):

    """
    MPODApalis Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    voltage_ramp_speed = Cpt(EpicsSignal, ':VoltageRampSpeed', kind='normal',
                             doc='MPOD module Voltage Ramp Rate [%/sec*Vnom]')

    current_ramp_speed = Cpt(EpicsSignal, ':CurrentRampSpeed', kind='normal',
                             doc='MPOD module current Ramp  Rate [%/sec*Inom]')

    temperature = Cpt(EpicsSignalRO, ':Temperature', kind='normal',
                      doc='MPOD Temperature [C]')

    supply_status = Cpt(EpicsSignalRO, ':isSupplyGood', kind='normal',
                        doc='Supply voltages are within range')

    module_status = Cpt(EpicsSignalRO, ':isModuleGood', kind='normal',
                        doc='Module health status')

    fine_adjustment_status = Cpt(EpicsSignalRO, ':isFineAdjustment',
                                 kind='normal', doc='Fine adjustment mode status')

    input_status = Cpt(EpicsSignalRO, ':isInputError', kind='normal',
                       doc='Input error in connection with a module access')

    live_insertion_status = Cpt(EpicsSignalRO, ':isLiveInsertion',
                                kind='normal', doc='Live insertion mode status')

    saftey_loop_status = Cpt(EpicsSignalRO, ':isSafetyLoopGood',
                             kind='normal', doc='Saftey loop status')

    kill = Cpt(EpicsSignal, ':isKillEnable',
               write_pv=':Control:setKillEnable',
               kind='normal', string=True,
               doc='Module-wide kill functionality')

    faults = Cpt(EpicsSignal, ':isEventActive',
                 write_pv=':Control:doClear',
                 kind='normal', string=True,
                 doc='Clears all MPOD module faults')

    limit_pos = Cpt(EpicsSignalRO, ':VoltageLimit', kind='omitted',
                    doc='Positive voltage limit as a % of the max voltage')

    limit_neg = Cpt(EpicsSignalRO, ':VoltageLimitNegative', kind='omitted',
                    doc='Negative voltage limit as a % of the max voltage')

    tab_component_names = True
    tab_whitelist = ['clear_faults', 'set_voltage_ramp_speed',
                     'set_current_ramp_speed']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._limit_pos = 0.0
        self._limit_neg = 0.0
        # tolerances for voltage limit tolerances (expected 0-100)
        # .5% relative change (of original value), and .5% absolute
        self._limit_rtol = 0.005
        self._limit_atol = 0.5

    def clear_faults(self):
        """Clears all module faults"""
        self.faults.put(1)

    def set_voltage_ramp_speed(self, ramp_speed):
        """
        Set the voltage ramp speed in %/sec*Vnom.

        It sets the voltage ramp speed for the entire card.

        Parameters
        ----------
        ramp_speed : number
            Voltage rise rate [%/sec*Vnom].
        """
        self.voltage_ramp_speed.put(ramp_speed)

    def set_current_ramp_speed(self, ramp_speed):
        """
        Set the current ramp speed in %/sec*Inom.

        It sets the current ramp speed for the entire card.

        Parameters
        ----------
        ramp_speed : number
            Current ramp speed [%/sec*Vnom].
        """
        self.current_ramp_speed.put(ramp_speed)

    @property
    def limit_percents(self) -> tuple[float, float]:
        """
        Returns limit percentage tuple.  Represents the % of the channel's max_voltage
        signal (:VoltageNominal) to be used as the actual limits for the channel

        Returns
        -------p
        tuple[float, float]
            The voltage limits as a proportion of the max_voltage
        """
        # negative limits are displayed as positive %
        limits = (-self._limit_neg, self._limit_pos)

        return limits

    def _update_channel_limits(self) -> None:
        """Signal all the MPODApalisChannel components to update their limits"""
        for cpt_name in self.component_names:
            cpt = getattr(self, cpt_name)
            if isinstance(cpt, MPODApalisChannel):
                cpt._update_max_voltage_limits()

    @limit_pos.sub_value
    def _update_limit_pos(self, value, **kwargs):
        if np.isclose(self._limit_pos, value,
                      rtol=self._limit_rtol, atol=self._limit_atol):
            return
        self._limit_pos = value
        self._update_channel_limits()

    @limit_neg.sub_value
    def _update_limit_neg(self, value, **kwargs):
        if np.isclose(self._limit_neg, value,
                      rtol=self._limit_rtol, atol=self._limit_atol):
            return
        self._limit_neg = value
        self._update_channel_limits()


class MPODApalisModule4Channel(MPODApalisModule):

    """
    MPODApalis 4 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")


class MPODApalisModule8Channel(MPODApalisModule):

    """
    MPODApalis 8 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")


class MPODApalisModule16Channel(MPODApalisModule):

    """
    MPODApalis 16 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")
    c8 = Cpt(MPODApalisChannel, ":C8")
    c9 = Cpt(MPODApalisChannel, ":C9")
    c10 = Cpt(MPODApalisChannel, ":C10")
    c11 = Cpt(MPODApalisChannel, ":C11")
    c12 = Cpt(MPODApalisChannel, ":C12")
    c13 = Cpt(MPODApalisChannel, ":C13")
    c14 = Cpt(MPODApalisChannel, ":C14")
    c15 = Cpt(MPODApalisChannel, ":C15")


class MPODApalisModule24Channel(MPODApalisModule):

    """
    MPODApalis 24 channel Module Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Module, e.g. 'TMO:MPOD:01:M6'.
    name : str
        A name to refer to the device.
    """

    c0 = Cpt(MPODApalisChannel, ":C0")
    c1 = Cpt(MPODApalisChannel, ":C1")
    c2 = Cpt(MPODApalisChannel, ":C2")
    c3 = Cpt(MPODApalisChannel, ":C3")
    c4 = Cpt(MPODApalisChannel, ":C4")
    c5 = Cpt(MPODApalisChannel, ":C5")
    c6 = Cpt(MPODApalisChannel, ":C6")
    c7 = Cpt(MPODApalisChannel, ":C7")
    c8 = Cpt(MPODApalisChannel, ":C8")
    c9 = Cpt(MPODApalisChannel, ":C9")
    c10 = Cpt(MPODApalisChannel, ":C10")
    c11 = Cpt(MPODApalisChannel, ":C11")
    c12 = Cpt(MPODApalisChannel, ":C12")
    c13 = Cpt(MPODApalisChannel, ":C13")
    c14 = Cpt(MPODApalisChannel, ":C14")
    c15 = Cpt(MPODApalisChannel, ":C15")
    c16 = Cpt(MPODApalisChannel, ":C16")
    c17 = Cpt(MPODApalisChannel, ":C17")
    c18 = Cpt(MPODApalisChannel, ":C18")
    c19 = Cpt(MPODApalisChannel, ":C19")
    c20 = Cpt(MPODApalisChannel, ":C20")
    c21 = Cpt(MPODApalisChannel, ":C21")
    c22 = Cpt(MPODApalisChannel, ":C22")
    c23 = Cpt(MPODApalisChannel, ":C23")


class MPODApalisCrate(BaseInterface, Device):

    """
    MPODApalis Crate Object.

    Parameters
    ----------
    card_prefix : str
        The EPICS base of the MPOD Crate, e.g. 'TMO:MPOD:01'.
    name : str
        A name to refer to the device.
    """

    power = Cpt(EpicsSignal, ':Crate:PowerOn',
                kind='normal', string=True,
                doc='Crate power status and control')

    tab_component_names = True
    tab_whitelist = ['power']

    def power_cycle(self):
        """
        Function used to power cycle the MPOD crate
        """
        self.power.put(0)
        time.sleep(5)
        self.power.put(1)
