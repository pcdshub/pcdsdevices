import copy
import functools
import typing

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.pseudopos import pseudo_position_argument, real_position_argument

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import FltMvInterface
from .pseudopos import PseudoPositioner, PseudoSingleInterface
from .signal import InternalSignal
from .sim import FastMotor


class QuadraticBeckhoffMotor(FltMvInterface, PseudoPositioner):
    """
    Pseudomotor of the form calc = ax^2 + bx + c.

    This represents a linear BeckhoffAxis that turns a crystal.
    The translation from linear (mm) motion to angular (mrad)
    motion can be approximated well by a best-fit polynomial
    of degree 2.

    Parameters
    ----------
    prefix : str
        The motor record prefix of the underlying real BeckhoffAxis.
    name : str, required keyword
        The name of the device to use as a reference.
    ca : float, required keyword
        The "a" constant in the best-fit polynomial.
    cb : float, required keyword
        The "b" constant in the best-fit polynomial.
    cc : float, required keyword
        The "c" constant in the best-fit polynomial.
    pol : -1 or 1, required keyword
        The polarity of the best-fit curve when converting back from
        calculated position to real position for requesting a move.
        The inverse of a quadratic function has two solutions at
        most points, so we need to pick which one is correct.
    limits : tuple of floats, required keyword
        The limits to enforce on moves of the calculated axis.
        This should be a tuple of size 2.
    """
    calc = Cpt(PseudoSingleInterface, egu='mrad', kind='hinted')
    real = Cpt(BeckhoffAxis, '', kind='omitted')

    # Aux signals for the typhos positioner widget
    _extra_sig_md = {
        'precision': 3,
        'units': 'mrad',
    }
    user_readback = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )
    user_setpoint = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )
    high_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )
    low_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind='omitted',
    )

    def __init__(
        self,
        prefix: str,
        *,
        name: str,
        ca: float,
        cb: float,
        cc: float,
        pol: int,
        limits: tuple[float, float],
        **kwargs
    ):
        self.ca = ca
        self.cb = cb
        self.cc = cc
        self.pol = pol
        super().__init__(prefix, name=name, **kwargs)
        self.calc._limits = limits
        self.low_limit_travel.put(limits[0], force=True)
        self.high_limit_travel.put(limits[1], force=True)
        self.real.user_readback.subscribe(
            functools.partial(
                self._calc_internal_update,
                internal_sig=self.user_readback,
            ),
        )
        self.real.user_setpoint.subscribe(
            functools.partial(
                self._calc_internal_update,
                internal_sig=self.user_setpoint,
            ),
        )

    @pseudo_position_argument
    def forward(self, pseudo_pos: typing.NamedTuple) -> typing.NamedTuple:
        """
        Calculate the position of the motor in mm given the mrad angle.

        This is called when we request a move and when we check if the
        position requested is within the limits of the linear motor.

        Note: it is possible for this to come up with a "nan" value if
        the input falls outside the bounds and gives us a negative
        in the sqrt function. However, during normal use, we can rely on
        the pseudo limits to keep us within the range that this
        calculation is valid and non-nan.
        """
        calc = pseudo_pos.calc
        real = (
            -self.cb
            + self.pol * np.sqrt(self.cb**2 - 4*self.ca*(self.cc - calc))
            ) / (2*self.ca)
        return self.RealPosition(real=real)

    @real_position_argument
    def inverse(self, real_pos: typing.NamedTuple) -> typing.NamedTuple:
        """
        Calculate the position of the crystal in mrad given the mm position.

        This is called when we check the current position of the
        PseudoPositioner.
        """
        real = real_pos.real
        calc = self.ca * real**2 + self.cb * real + self.cc
        return self.PseudoPosition(calc=calc)

    def _calc_internal_update(
        self,
        internal_sig: InternalSignal,
        value: float,
        **kwargs
    ):
        """
        Callback to update InternalSignal elements for the typhos UI.

        This simply does the inverse calculation based on the given
        mm value in order to put the mrad value into the
        pre-registered signal.
        """
        calc = self.inverse(self.RealPosition(real=value)).calc
        internal_sig.put(calc, force=True)


class QuadraticSimMotor(QuadraticBeckhoffMotor):
    """Simulated version of the QuadraticBeckhoffMotor for offline testing."""
    real = Cpt(FastMotor, kind='omitted')


class VLSOptics(GroupDevice):
    """
    Device that collects the VLS mirror and grating together.

    This also defines their polynomial fit constants, polarities, and limits.

    Parameters
    ----------
    prefix : str,
        This value is currently unused.
    name : str, required keyword
        This value is used to name the subcomponents.
    """
    mirror = Cpt(
        QuadraticBeckhoffMotor,
        "CRIX:VLS:MMS:MP",
        ca=-0.7569,
        cb=18.100,
        cc=27.667,
        pol=1,
        limits=(5.275, 41.882),
        kind='hinted',
    )
    grating = Cpt(
        QuadraticBeckhoffMotor,
        "CRIX:VLS:MMS:GP",
        ca=0.334,
        cb=-16.25,
        cc=22.56,
        pol=-1,
        limits=(3.541, 51.8462),
        kind='hinted',
    )


class VLSOpticsSim(VLSOptics):
    """Simulated version of VLSOptics for offline testing."""
    mirror = copy.copy(VLSOptics.mirror)
    mirror.cls = QuadraticSimMotor
    grating = copy.copy(VLSOptics.grating)
    grating.cls = QuadraticSimMotor

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mirror.real.move(0)
        self.grating.real.move(20)
