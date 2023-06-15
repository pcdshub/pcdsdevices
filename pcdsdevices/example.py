"""
Example devices that don't correspond to any real hardware,
but may correspond to real IOCs that simulate hardware.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal

from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis
from .inout import TwinCATInOutPositioner
from .interface import BaseInterface
from .pim import XPIM
from .pmps import TwinCATStatePMPS


class Example3DStates(TwinCATStatePMPS):
    """
    3D States with PMPS, simluated XYZ
    """
    config = UpCpt(state_count=3, motor_count=3)


class Example3D(BaseInterface, Device):
    # Standalone setpoints for the top of the demo typhos display
    xsp = Cpt(EpicsSignal, "X.RBV", write_pv="X.VAL")
    ysp = Cpt(EpicsSignal, "Y.RBV", write_pv="Y.VAL")
    zsp = Cpt(EpicsSignal, "Z.RBV", write_pv="Z.VAL")
    # The core states object
    states = Cpt(Example3DStates, "STATES")
    # Full motor widgets for the bottom of the demo typhos display
    xmot = Cpt(BeckhoffAxis, "X")
    ymot = Cpt(BeckhoffAxis, "Y")
    zmot = Cpt(BeckhoffAxis, "Z")


class ExampleL2LStates(TwinCATInOutPositioner):
    """
    1D States, no PMPS, limit to limit instead of state based

    Note: the limit-to-limit move is implemented on the PLC-side
    """
    config = UpCpt(state_count=2, motor_count=1)


class ExampleL2L(TwinCATInOutPositioner):
    # Standalone setpoints for the top of the demo typhos display
    sp = Cpt(EpicsSignal, "MOT.RBV", write_pv="MOT.VAL")
    # The core states object
    states = Cpt(ExampleL2LStates, "STATES")
    # Full motor widgets for the bottom of the demo typhos display
    mot = Cpt(BeckhoffAxis, "MOT")


class PLCExampleMotion(BaseInterface, Device):
    """
    This matches the IOC for lcls-plc-example-motion
    """
    mot1 = Cpt(BeckhoffAxis, "01")
    mot2 = Cpt(BeckhoffAxis, "02")
    mot3 = Cpt(BeckhoffAxis, "03")
    xpim = FCpt(XPIM, "IMTST:XTES")
    sim3d = Cpt(Example3D, "3D:")
    siml2l = Cpt(ExampleL2L, "L2L:")

    def __init__(self, prefix: str = "PLC:TST:MOT:", name: str = "plc_example_motion"):
        super().__init__(prefix, name=name)
