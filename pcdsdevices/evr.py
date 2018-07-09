from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, Kind


class Trigger(Device):
    """
    Class for an individual Trigger
    """
    eventcode = Cpt(EpicsSignal, ':EC_RBV', write_pv=':TEC', kind=Kind.config)
    eventrate = Cpt(EpicsSignalRO, ':RATE', kind=Kind.normal)
    label = Cpt(EpicsSignal, ':TCTL.DESC', kind=Kind.omitted)
    ns_delay = Cpt(EpicsSignal, ':BW_TDES', write_pv=':TDES', kind=Kind.hinted)
    polarity = Cpt(EpicsSignal, ':TPOL', kind=Kind.config)
    width = Cpt(EpicsSignal, ':BW_TWIDCALC', write_pv=':TWID',
                kind=Kind.normal)
    enable_cmd = Cpt(EpicsSignal, ':TCTL', kind=Kind.omitted)

    def enable(self):
        """Enable the trigger"""
        self.enable_cmd.put(1)

    def disable(self):
        """Disable the trigger"""
        self.enable_cmd.put(0)
