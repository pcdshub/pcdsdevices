"""
Basic Beryllium Lens XFLS
"""
# flake8: noqa
from ophyd.device import Component as Cpt, FormattedComponent as FCpt, Device
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             pseudo_position_argument, real_position_argument)

from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .sim import FastMotor


class XFLS(InOutRecordPositioner):
    """
    XRay Focusing Lens (Be)

    This is the simple version where the lens positions are named by number.
    """
    __doc__ += basic_positioner_init

    states_list = ['LENS1', 'LENS2', 'LENS3', 'OUT']
    in_states = ['LENS1', 'LENS2', 'LENS3']
    _lens_transmission = 0.8

    def __init__(self, prefix, *, name, **kwargs):
        # Set a default transmission, but allow easy subclass overrides
        for state in self.in_states:
            self._transmission[state] = self._lens_transmission
        super().__init__(prefix, name=name, **kwargs)


# Change into PseudoPositioner when it's time to add the calculations
class LensStack(Device):
    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')

    def __init__(self, x_prefix, y_prefix, z_prefix, *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        super().__init__(x_prefix, *args, **kwargs)


class SimLensStack(LensStack):
    """
    Test version of the lens stack for testing the Be lens class.
    """
    x = Cpt(FastMotor, limits=(-10, 10))
    y = Cpt(FastMotor, limits=(-10, 10))
    z = Cpt(FastMotor, limits=(-100, 100))
