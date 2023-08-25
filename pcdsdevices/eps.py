"""
Classes for Equipment Protection System (EPS) readbacks.

This covers generalized ways that we can protect hardware from
damaging itself. For example: we can prevent a motor from moving
forward if moving forward would collide with another motor.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import InternalSignal, PytmcSignal
from .variety import set_metadata


class EPS(BaseInterface, Device):
    """
    Corresponds to DUT_EPS from lcls-twincat-general.

    This struct represents a combined EPS status that can be
    made up of many independent protection factors. It summarizes
    all of the EPS information in a way that can be consumed
    by higher level applications so that the user knows exactly
    why their motor cannot move, why their valve cannot open,
    etc.

    This has a corresponding EPS widget in pcdswidgets, so
    this class only makes minimal adjustments to make the default
    typhos view usable.
    """
    eps_ok = Cpt(PytmcSignal, "bEPS_OK", io="i", kind="normal",
                 doc="EPS summary: true if everything is OK")
    message = Cpt(PytmcSignal, "sMessage", io="i", kind="normal",
                  string=True,
                  doc="Message from EPS to the user.")
    flags_raw = Cpt(PytmcSignal, "nFlags", io="i", kind="omitted",
                    doc="Raw EPS bitmask")
    flags = Cpt(InternalSignal, kind="normal")
    flag_desc = Cpt(PytmcSignal, "sFlagDesc", io="i", kind="omitted",
                    string=True,
                    doc="Semicolon-delimited descriptions of each flag")

    # See _update_flag docstring
    set_metadata(flags, dict(variety="bitmask", bits=8))

    @flags_raw.sub_value
    def _update_flag(self, value, *args, **kwargs):
        """
        Update the flags value to a form that is usable in a pydm bitmask.

        If bit 32 is TRUE, this comes as a negative number because EPICS CA has
        no unsigned types, so the 32-bit UINT is cast to a 32-bit int.

        For some reason, the PyDM bitmask widget reapplies this conversion, so
        I can't actually display the 32nd bit without blanking out the whole
        bitmask widget.

        The 32nd bit will literally never be used, but we can truncate at the 31st
        bit so that we get a usable widget.

        Further, most of these are unlikely to get use. What kind of motor has
        31 EPS considerations? Surely that motor would have a special screen.

        For this case we'll truncate all the way to 8 bits.
        """
        if value < 0:
            value = 2**8 + value
        self.flags.put(value, force=True)
