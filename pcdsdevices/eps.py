"""
Classes for EPS readbacks.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import PytmcSignal


class EPS(BaseInterface, Device):
    """
    Corresponds to DUT_EPS from lcls-twincat-general.

    This struct represents a combined EPS status that can be
    made up of many independent protection factors. It summarizes
    all of the EPS information in a way that can be consumed
    by higher level applications so that the user knows exactly
    why their motor cannot move, why their valve cannot open,
    etc.
    """
    eps_ok = Cpt(PytmcSignal, "bEPS_OK", io="io", kind="normal",
                 doc="EPS summary: true if everything is OK")
    message = Cpt(PytmcSignal, "sMessage", io="i", kind="normal",
                  doc="Message from EPS to the user.")
    flags = Cpt(PytmcSignal, "nFlags", io="i", kind="omitted",
                doc="Raw EPS bitmask")
    flag_desc = Cpt(PytmcSignal, "sFlagDesc", io="i", kind="omitted",
                    doc="Semicolon-delimited descriptions of each flag")
