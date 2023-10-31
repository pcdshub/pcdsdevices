from enum import Enum

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface
from .pv_positioner import PVPositionerIsClose
from .signal import MultiDerivedSignal, MultiDerivedSignalRO
from .type_hints import SignalToValue
from .variety import set_metadata

TPR_TICK_NS = 5.384
TPR_TAP_NS = 0.08


class TimingMode(Enum):
    LCLS1 = 1
    LCLS2 = 2


def _get_delay(mds: MultiDerivedSignal, items: SignalToValue) -> float:
    """Calculates delay in ns from ticks and taps"""
    return items[mds.attrs[0]] * TPR_TICK_NS + items[mds.attrs[1] * TPR_TAP_NS]


def _get_width(mds: MultiDerivedSignal, items: SignalToValue) -> float:
    """Calculates width in ns from ticks"""
    return items[mds.attrs[0]] * TPR_TICK_NS


def _put_last(mds: MultiDerivedSignal, value: float) -> SignalToValue:
    """Only writes value to last attr"""
    return {mds.attrs[-1]: value}


class TprMotor(PVPositionerIsClose):
    """
    PV Positioner for adjusting an TPR channel.

    Moves that are less than one tick
    are considered immediately complete.
    """
    setpoint = FCpt(EpicsSignal, "{self.prefix}{self.sys}TDES", kind="normal", doc="Trigger delay setpoint in nsec")
    delay_ticks = FCpt(EpicsSignal, '{self.prefix}TDESTICKS', kind="omitted", doc="Trigger delay in clock ticks")
    delay_taps = FCpt(EpicsSignal, '{self.prefix}TDESTAPS', kind="omitted", doc="Trigger delay in delay taps")
    readback = Cpt(
        MultiDerivedSignalRO,
        attrs=['delay_ticks', 'delay_taps'],
        calculate_on_get=_get_delay
    )
    atol = TPR_TICK_NS
    rtol = 0

    def __init__(self, prefix, *, sys, name, **kwargs):
        self.prefix = prefix
        self.sys = sys
        super().__init__(prefix, name=name, **kwargs)


class TprTrigger(BaseInterface, Device):
    """Class for an individual TprTrigger."""
    ratemode = FCpt(EpicsSignal, '{self.prefix}{self.ch}RATEMODE', kind="config", doc="Channel rate mode selector")
    group = FCpt(EpicsSignal, '{self.prefix}{self.ch}GROUP', kind="omitted", doc="Channel group Bit")
    seqcode = FCpt(EpicsSignal, '{self.prefix}{self.ch}SEQCODE', kind="omitted", doc="Channel sequence code")
    fixedrate = FCpt(EpicsSignal, '{self.prefix}{self.ch}FIXEDRATE', kind="omitted", doc="Channel Fxed rate selector")
    count = FCpt(EpicsSignal, '{self.prefix}{self.ch}CNT', kind="omitted", doc="Channel counter")
    destmask = FCpt(EpicsSignal, '{self.prefix}{self.ch}DESTMASK', kind="omitted", doc="Channel destination mask")
    destmode = FCpt(EpicsSignal, '{self.prefix}{self.ch}DESTMODE', kind="omitted", doc="Channel destination mode selector")
    src = FCpt(EpicsSignal, '{self.prefix}{self.trg}SOURCE', kind="omitted", doc="Trigger source")
    eventcode = FCpt(EpicsSignal, '{self.prefix}{self.ch}EVCODE', kind="config", doc="Channel LCLS1 event code")
    eventrate = FCpt(EpicsSignalRO, '{self.prefix}{self.ch}RATE', kind="normal", doc="Channel event rates")
    label = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL.DESC', kind="omitted", doc="Enable/disable")
    delay_ticks = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTICKS', kind="omitted", doc="Trigger delay in clock ticks")
    delay_taps = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTAPS', kind="omitted", doc="Trigger delay in delay taps")
    delay_setpoint = FCpt(EpicsSignal, '{self.prefix}{self.trg}{self.sys}TDES', kind="omitted", doc="Trigger delay setpoint in nsec")
    ns_delay = Cpt(
        MultiDerivedSignal,
        attrs=['delay_ticks', 'delay_taps', 'delay_setpoint'],
        calculate_on_get=_get_delay,
        calculate_on_put=_put_last,
        doc="Get/set trigger delay in ns",
    )
    ns_delay_scan = FCpt(TprMotor, '{self.prefix}{self.trg}', sys='{self.sys}', kind="omitted", doc="Motor-like tpr interface")
    polarity = FCpt(EpicsSignal, '{self.prefix}{self.trg}TPOL', kind="config", doc="Trigger description")
    width_setpoint = FCpt(EpicsSignal, '{self.prefix}{self.trg}{self.sys}TWID', kind="omitted", doc="Trigger width in ns")
    width_ticks = FCpt(EpicsSignalRO, '{self.prefix}{self.trg}TWIDTICKS', kind="omitted", doc="Trigger width in clock ticks")
    width = Cpt(
        MultiDerivedSignal,
        attrs=['width_ticks', 'width_setpoint'],
        calculate_on_get=_get_width,
        calculate_on_put=_put_last,
        doc="Get/set trigger width in nsec",
    )
    enable_ch_cmd = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL', kind="omitted", doc="Channel enable/disable")
    set_metadata(enable_ch_cmd, dict(variety='command-proc', value=1))
    enable_trg_cmd = FCpt(EpicsSignal, '{self.prefix}{self.trg}{self.sys}TCTL', kind="omitted", doc="Trigger enable/disable")
    set_metadata(enable_trg_cmd, dict(variety='command-proc', value=1))

    tab_whitelist = ['enable', 'disable']
    tab_component_names = True

    def __init__(self, prefix, *, channel, timing_mode, name, **kwargs):
        if timing_mode == TimingMode.LCLS1:
            self.sys = 'SYS0_'
        elif timing_mode == TimingMode.LCLS2:
            self.sys = 'SYS2_'
        else:
            raise TypeError("timing_mode must be TimingMode.LCLS1 or TimingMode.LCLS2")
        self.ch = f':CH{channel:02}_'
        self.trg = f':TRG{channel:02}_'
        super().__init__(prefix, name=name, **kwargs)

    def enable(self):
        """Enable the channel and trigger."""
        self.enable_ch()
        self.enable_trg()

    def disable(self):
        """Disable the channel and trigger."""
        self.disable_ch()
        self.disable_trg()

    def enable_ch(self):
        """Enable the channel."""
        self.enable_ch_cmd.put(1)

    def disable_ch(self):
        """Disable the channel."""
        self.enable_ch_cmd.put(0)

    def enable_trg(self):
        """Enable the trigger."""
        self.enable_trg_cmd.put(1)

    def disable_trg(self):
        """Disable the trigger."""
        self.enable_trg_cmd.put(0)
