import logging
import time
from enum import Enum, auto

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
        Set explicit symmetric limits on voltage for better error reporting.

        Refers to the parent module if it exists, to determine the limit scaling

        If not, defaults to setting limits to positive definite
        """
        polarity = getattr(self, "biological_parent.polarity", Polarity.POSITIVE)
        limit_scales = getattr(self, "biological_parent.limit_scales", (0, 100))
        limits = [lim * self._max_voltage / 100 for lim in limit_scales]

        if polarity is Polarity.BIPOLAR:
            if 0 in limits:
                logger.debug(f"Bipolar limits expected, got: ({limits})")
        elif polarity is Polarity.NEGATIVE:
            if all(lim >= 0 for lim in limits):
                logger.debug(f"Negative limits expected, got: ({limits})")
        elif polarity is Polarity.POSITIVE:
            if all(lim <= 0 for lim in limits):
                logger.debug(f"Positive limits expected, got: ({limits})")

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


class Polarity(Enum):
    POSITIVE = auto()
    NEGATIVE = auto()
    BIPOLAR = auto()


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

    model = Cpt(EpicsSignalRO, ':Model', kind='omitted', string=True,
                doc="Model number")

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
        self._model_str = ''

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

    @model.sub_value
    def _stash_model(self, value, **kwargs) -> None:
        self._model_str = self.model.get()

    @property
    def polarity(self) -> Polarity:
        if self._model_str.endswith("x"):
            return Polarity.BIPOLAR
        elif self._model_str.endswith("p"):
            return Polarity.POSITIVE
        elif self._model_str.endswith("n"):
            return Polarity.NEGATIVE

        raise ValueError(f"Unable to determine module polarity: {self._model_str}")

    @property
    def limit_scales(self) -> tuple[float, float]:
        """
        Returns limit scaling tuple.  When multiplied by the channel's max_voltage
        signal (:VoltageNominal) will produce the actual limits for the channel

        Returns
        -------
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
        self._limit_pos = value
        self._update_channel_limits()

    @limit_neg.sub_value
    def _update_limit_neg(self, value, **kwargs):
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
