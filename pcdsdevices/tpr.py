from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface
from .pv_positioner import PVPositionerIsClose
from .signal import MultiDerivedSignal
from .type_hints import SignalToValue

TPR_TICK_NS = 5.384
TPR_TAP_NS = 0.08


def _get_delay(mds: MultiDerivedSignal, items: SignalToValue) -> float:
    return items[mds.attrs[0]] * TPR_TICK_NS + items[mds.attrs[1] * TPR_TAP_NS]


def _get_width(mds: MultiDerivedSignal, items: SignalToValue) -> float:
    return items[mds.attrs[0]] * TPR_TICK_NS


def _put_last(mds: MultiDerivedSignal, value: float) -> SignalToValue:
    return {mds.attrs[-1]: value}


class TprMotor(PVPositionerIsClose):
    """
    PV Positioner for adjusting an TPR channel.

    Moves that are less than one tick
    are considered immediately complete.
    """
    setpoint = FCpt(EpicsSignal, "{self.prefix}{self.sys}TDES", kind="normal")
    readback = Cpt(EpicsSignalRO, ":BW_TDES", kind="hinted")
    atol = TPR_TICK_NS
    rtol = 0

    def __init__(self, prefix, *, sys, name, **kwargs):
        self.sys = sys
        super().__init__(prefix, name=name, **kwargs)


class TprTrigger(BaseInterface, Device):
    """Class for an individual TprTrigger."""
    eventcode = FCpt(EpicsSignal, '{self.prefix}{self.ch}EVCODE', kind="config")
    eventrate = FCpt(EpicsSignalRO, '{self.prefix}{self.ch}RATE', kind="normal")
    label = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL.DESC', kind="omitted")
    label2 = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys2}TCTL.DESC', kind="omitted")
    ns_delay = FCpt(
        EpicsSignal,
        ':BW_TDES',
        write_pv=':TDES',
        tolerance=TPR_TICK_NS,
        kind="hinted",
    )
    ns_delay_scan = FCpt(TprMotor, '', sys='{self.sys}', kind="omitted")
    polarity = FCpt(EpicsSignal, '{self.prefix}{self.trg}TPOL', kind="config")
    width = FCpt(
        MultiDerivedSignal,
        attrs=['{self.prefix}{self.trg}TWIDTICKS', '{self.prefix}{self.sys}TWID'],
        calculate_on_get=_get_width,
        calculate_on_put=_put_last,
    )
    enable_cmd = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys}TCTL', kind="omitted")
    enable_cmd2 = FCpt(EpicsSignal, '{self.prefix}{self.ch}{self.sys2}TCTL', kind="omitted")

    tab_whitelist = ['enable', 'disable']
    tab_component_names = True

    def __init__(self, prefix, *, channel, name, **kwargs):
        self.ch = f':CH{channel:02}_'
        self.trg = f':TRG{channel:02}_'
        self.sys = 'SYS0_'
        self.sys2 = 'SYS2_'
        super().__init__(prefix, name=name, **kwargs)

    def enable(self):
        """Enable the trigger."""
        self.enable_cmd.put(1)

    def disable(self):
        """Disable the trigger."""
        self.enable_cmd.put(0)
