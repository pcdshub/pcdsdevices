from ophyd import Component as Cpt
from ophyd import Device

from .interface import BaseInterface
from .signal import PytmcSignal


class J120K(BaseInterface, Device):
    """
    A class representing the J120K 24V dry contact cooling flow switch.
    """
    flow_ok = Cpt(PytmcSignal, ':FSW:FLOW_OK', io='i',
                  kind='normal', doc='flow rate nominal')
