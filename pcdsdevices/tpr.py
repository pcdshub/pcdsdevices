from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface
from .pv_positioner import PVPositionerIsClose
from .signal import MultiDerivedSignal, MultiDerivedSignalRO
from .type_hints import SignalToValue

TPR_TICK_NS = 5.384
TPR_TAP_NS = 0.08


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
    setpoint = FCpt(EpicsSignal, "{self.prefix}{self.sys}TDES", kind="normal")
    delay_ticks = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTICKS', kind="omitted")
    delay_taps = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTAPS', kind="omitted")
    readback = Cpt(
        MultiDerivedSignalRO,
        attrs=['delay_ticks', 'delay_taps'],
        calculate_on_get=_get_delay
    )
    atol = TPR_TICK_NS
    rtol = 0

    def __init__(self, prefix, *, sys, trg, name, **kwargs):
        self.prefix = prefix
        self.sys = sys
        self.trg = trg
        super().__init__(prefix, name=name, **kwargs)


class TprTrigger(BaseInterface, Device):
    """Class for an individual TprTrigger."""
    ratemode = FCpt(EpicsSignal, '{self.prefix}{self.ch}RATECODE', kind="config")
    group = FCpt(EpicsSignal, '{self.prefix}{self.ch}GROUP', kind="omitted")
    seqcode = FCpt(EpicsSignal, '{self.prefix}{self.ch}SEQCODE', kind="omitted")
    fixedrate = FCpt(EpicsSignal, '{self.prefix}{self.ch}FIXEDRATE', kind="omitted")
    count = FCpt(EpicsSignal, '{self.prefix}{self.ch}COUNT', kind="omitted")
    destmask = FCpt(EpicsSignal, '{self.prefix}{self.ch}DESTMASK', kind="omitted")
    destmode = FCpt(EpicsSignal, '{self.prefix}{self.ch}DESTMODE', kind="omitted")
    src = FCpt(EpicsSignal, '{self.prefix}{self.trg}SOURCE', kind="omitted")
    eventcode = FCpt(EpicsSignal, '{self.prefix}{self.ch}EVCODE', kind="config")
    eventrate = FCpt(EpicsSignalRO, '{self.prefix}{self.ch}RATE', kind="normal")
    label = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL.DESC', kind="omitted")
    label2 = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys2}TCTL.DESC', kind="omitted")
    delay_ticks = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTICKS', kind="omitted")
    delay_taps = FCpt(EpicsSignal, '{self.prefix}{self.trg}TDESTAPS', kind="omitted")
    delay_setpoint = FCpt(EpicsSignal, '{self.prefix}{self.sys}TDES', kind="omitted")
    delay_setpoint2 = FCpt(EpicsSignal, '{self.prefix}{self.sys2}TDES', kind="omitted")
    ns_delay = Cpt(
        MultiDerivedSignal,
        attrs=['delay_ticks', 'delay_taps', 'delay_setpoint'],
        calculate_on_get=_get_delay,
        calculate_on_put=_put_last,
    )
    ns_delay2 = Cpt(
        MultiDerivedSignal,
        attrs=['delay_ticks', 'delay_taps', 'delay_setpoint2'],
        calculate_on_get=_get_delay,
        calculate_on_put=_put_last,
    )
    ns_delay_scan = FCpt(TprMotor, '{self.prefix}', sys='{self.sys}', trg='{self.trg}', kind="omitted")
    ns_delay_scan2 = FCpt(TprMotor, '{self.prefix}', sys='{self.sys2}', trg='{self.trg}', kind="omitted")
    polarity = FCpt(EpicsSignal, '{self.prefix}{self.trg}TPOL', kind="config")
    width_setpoint = FCpt(EpicsSignal, '{self.prefix}{self.sys}TWID', kind="omitted")
    width_setpoint2 = FCpt(EpicsSignal, '{self.prefix}{self.sys2}TWID', kind="omitted")
    width_ticks = FCpt(EpicsSignalRO, '{self.prefix}{self.trg}TWIDTICKS', kind="omitted")
    width = Cpt(
        MultiDerivedSignal,
        attrs=['width_ticks', 'width_setpoint'],
        calculate_on_get=_get_width,
        calculate_on_put=_put_last,
    )
    width2 = Cpt(
        MultiDerivedSignal,
        attrs=['width_ticks', 'width_setpoint2'],
        calculate_on_get=_get_width,
        calculate_on_put=_put_last,
    )
    enable_cmd = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL', kind="omitted")
    enable_cmd2 = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys2}TCTL', kind="omitted")

    tab_whitelist = ['enable', 'disable']
    tab_component_names = True

    def __init__(self, prefix, *, channel, name, **kwargs):
        self.sys = 'SYS0_'
        self.sys2 = 'SYS2_'
        self.ch = f':CH{channel:02}_'
        self.trg = f':TRG{channel:02}_'
        super().__init__(prefix, name=name, **kwargs)

    def enable(self):
        """Enable the trigger."""
        self.enable_cmd.put(1)

    def disable(self):
        """Disable the trigger."""
        self.enable_cmd.put(0)
