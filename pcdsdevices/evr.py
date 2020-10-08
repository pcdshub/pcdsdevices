from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface


class Trigger(BaseInterface, Device):
    """Class for an individual Trigger."""
    eventcode = Cpt(EpicsSignal, ':EC_RBV', write_pv=':TEC', kind="config")
    eventrate = Cpt(EpicsSignalRO, ':RATE', kind="normal")
    label = Cpt(EpicsSignal, ':TCTL.DESC', kind="omitted")
    ns_delay = Cpt(EpicsSignal, ':BW_TDES', write_pv=':TDES', kind="hinted")
    polarity = Cpt(EpicsSignal, ':TPOL', kind="config")
    width = Cpt(EpicsSignal, ':BW_TWIDCALC', write_pv=':TWID', kind="normal")
    enable_cmd = Cpt(EpicsSignal, ':TCTL', kind="omitted")

    tab_whitelist = ['enable', 'disable']
    tab_component_names = True

    def enable(self):
        """Enable the trigger."""
        self.enable_cmd.put(1)

    def disable(self):
        """Disable the trigger."""
        self.enable_cmd.put(0)
