"""
Offset Mirror Classes.

This module contains all the classes relating to the offset mirrors used in the
FEE and XRT. Each offset mirror contains a stepper motor and piezo motor to
control the pitch, and two pairs of motors to control the horizontal and
vertical gantries.
"""
import logging
from typing import List, Tuple, Union

import numpy as np
from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt
from ophyd import PVPositioner

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .doc_stubs import basic_positioner_init
from .epics_motor import BeckhoffAxisNoOffset
from .inout import InOutRecordPositioner
from .interface import BaseInterface, FltMvInterface, LightpathMixin
from .pmps import TwinCATStatePMPS
from .signal import PytmcSignal
from .utils import get_status_value, reorder_components, schedule_task

logger = logging.getLogger(__name__)


numeric = Union[int, float]


class MirrorLogicError(Exception):
    """ An error in mirror pointing logic """


class OMMotor(FltMvInterface, PVPositioner):
    """Base class for each motor in the LCLS offset mirror system."""
    __doc__ += basic_positioner_init

    # position
    readback = Cpt(EpicsSignalRO, ':RBV', auto_monitor=True, kind='hinted')
    setpoint = Cpt(EpicsSignal, ':VAL', auto_monitor=True, limits=True,
                   kind='normal')
    done = Cpt(EpicsSignalRO, ':DMOV', auto_monitor=True, kind='omitted')
    motor_egu = Cpt(EpicsSignal, ':RBV.EGU', kind='omitted')

    # status
    interlock = Cpt(EpicsSignalRO, ':INTERLOCK', kind='omitted')
    enabled = Cpt(EpicsSignalRO, ':ENABLED', kind='omitted')
    # limit switches
    low_limit_switch = Cpt(EpicsSignalRO, ":LLS", kind='omitted')
    high_limit_switch = Cpt(EpicsSignalRO, ":HLS", kind='omitted')

    @property
    def egu(self):
        """
        Returns the Engineering Units of the readback PV, as reported by EPICS.
        """
        return self.motor_egu.get()

    def check_value(self, position):
        """
        Checks that the value is both valid and within the motor's soft limits.

        Parameters
        ----------
        position : float
            Position to check for validity.

        Raises
        ------
        ValueError
            If position is `None`, `~numpy.NaN` or `~numpy.Inf`.

        LimitError
            If the position is outside the soft limits.
        """

        # Check that we do not have a NaN or an Inf as those will
        # will make the PLC very unhappy ...
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))
        # Use the built-in PVPositioner check_value
        super().check_value(position)


class Pitch(OMMotor):
    """
    HOMS Pitch Mechanism.

    The axis is actually a piezo actuator and a stepper motor in series, and
    this is reflected in the PV naming.
    """

    __doc__ += basic_positioner_init

    piezo_volts = FCpt(EpicsSignalRO, "{self._piezo}:VRBV", kind='normal')
    stop_signal = FCpt(EpicsSignal, "{self._piezo}:STOP", kind='omitted')
    # TODO: Limits will be added soon, but not present yet

    def __init__(self, prefix, **kwargs):
        # Predict the prefix of all piezo pvs
        self._piezo = prefix.replace('MIRR', 'PIEZO')
        super().__init__(prefix, **kwargs)


class Gantry(OMMotor):
    """
    Gantry Axis.

    The horizontal and vertical motion of the OffsetMirror are controlled by
    two coupled stepper motors. Instructions are sent to both by simply
    requesting a move on the primary so they are represented here as a single
    motor with additional diagnostics and interlock.

    Parameters
    ----------
    prefix : str
        Base prefix for both stepper motors e.g. 'XRT:M1H'. Do not include the
        'P' or 'S' to indicate primary or secondary steppers.

    gantry_prefix : str, optional
        Prefix for the shared gantry diagnostics if it is different than the
        stepper motor prefix.
    """

    # Readbacks for gantry information
    gantry_difference = FCpt(EpicsSignalRO, '{self.gantry_prefix}:GDIF',
                             kind='normal')
    decoupled = FCpt(EpicsSignalRO, '{self.gantry_prefix}:DECOUPLE',
                     kind='config')
    # Readbacks for the secondary motor
    follower_readback = FCpt(EpicsSignalRO, '{self.follow_prefix}:RBV',
                             kind='normal')
    follower_low_limit_switch = FCpt(EpicsSignalRO, '{self.follow_prefix}:LLS',
                                     kind='omitted')
    follower_high_limit_switch = FCpt(EpicsSignalRO,
                                      '{self.follow_prefix}:HLS',
                                      kind='omitted')

    def __init__(self, prefix, *, gantry_prefix=None, **kwargs):
        self.gantry_prefix = gantry_prefix or 'GANTRY:' + prefix
        self.follow_prefix = prefix + ':S'
        super().__init__(prefix + ':P', **kwargs)

    def check_value(self, pos):
        """
        Add additional check for the gantry coupling.

        This is not a safety measure, but instead just here largely
        for bookkeeping and to give the operator further feedback on why the
        requested move is not completed.
        """

        # Check that the gantry is not decoupled
        if self.decoupled.get():
            raise PermissionError("The gantry is not currently coupled")
        # Allow OMMotor to check the value
        super().check_value(pos)


class OffsetMirror(BaseInterface, GroupDevice, LightpathMixin):
    """
    X-ray Offset Mirror class.

    This is for each individual mirror system used in the FEE
    and XRT. Controls for the pitch, and primary gantry x- and y-motors are
    included.

    When controlling the pitch motor, if the piezo is set to 'PID' mode, then
    the pitch mechanism is setup to first move the stepper as close to the
    desired position, then the piezo will kick in to constantly try and correct
    any positional changes.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the pitch motor.

    prefix_xy : str
        The EPICS base PV of the gantry x and y gantry motors.

    xgantry_prefix : str
        The name of the horizontal gantry if not identical to the prefix.

    name : str
        The name of the offset mirror.
    """

    # Pitch Motor
    pitch = FCpt(Pitch, "MIRR:{self.prefix}", kind='hinted')
    # Gantry motors
    xgantry = FCpt(Gantry, "{self._prefix_xy}:X",
                   gantry_prefix="{self._xgantry}",
                   add_prefix=['suffix', 'gantry_prefix'],
                   kind='normal')
    ygantry = FCpt(Gantry, "{self._prefix_xy}:Y",
                   gantry_prefix='GANTRY:{self.prefix}:Y',
                   add_prefix=['suffix', 'gantry_prefix'],
                   kind='config')
    # Transmission for Lightpath Interface
    transmission = 1.0
    # QIcon for UX
    _icon = 'fa.minus-square'
    # Subscription types
    SUB_STATE = 'state'

    lightpath_cpts = ['pitch.readback']

    # Tab config: show components
    tab_component_names = True

    def __init__(self, prefix, *, prefix_xy=None,
                 xgantry_prefix=None, **kwargs):
        # Handle prefix mangling
        self._prefix_xy = prefix_xy or prefix
        self._xgantry = xgantry_prefix or 'GANTRY:' + prefix + ':X'
        super().__init__(prefix, **kwargs)

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )

    @property
    def inserted(self):
        """Returns `True`. Treats OffsetMirror as always inserted."""
        return True

    @property
    def removed(self):
        """Returns :keyword:`False`. Treats OffsetMirror as always inserted."""
        return False

    def format_status_info(self, status_info):
        """
        Override status info handler to render the `OffsetMirror`.

        Display `OffsetMirror` status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        # happi metadata
        try:
            md = self.root.md
        except AttributeError:
            name = f'{self.prefix}'
        else:
            beamline = get_status_value(md, 'beamline')
            functional_group = get_status_value(md, 'functional_group')
            if functional_group is not None:
                name = f'{self.prefix} ({beamline} {functional_group})'
            else:
                name = f'{self.prefix} ({beamline})'

        p_position = get_status_value(status_info, 'pitch', 'position')
        p_setpoint = get_status_value(status_info, 'pitch',
                                      'setpoint', 'value')
        p_units = get_status_value(status_info, 'pitch', 'setpoint',
                                   'units')
        return f"""\
{name}
------
pitch: ({self.pitch.prefix})
------
    position: {p_position}
    setpoint: {p_setpoint} [{p_units}]
"""


class PointingMirror(InOutRecordPositioner, OffsetMirror):
    """
    Retractable `OffsetMirror`.

    Both XRT M1H and XRT M2H can be completely removed from the beam depending
    on the beam destination. In this case, the X gantry can be controlled via
    the standard PCDS states record. This class has all the functionality of
    `OffsetMirror` with the addition of the records that control the
    overall state.

    Parameters
    ----------
    in_lines : list, optional
        List of beamlines that are delivered beam when the mirror is in.

    out_lines : list, optional
        List of beamlines thate are delivered beam when the mirror is out.
    """

    # Reverse state order as PointingMirror is non-standard
    states_list = ['OUT', 'IN']
    # Moving PointingMirror moves the x gantry
    stage_group = [OffsetMirror.xgantry]

    def __init__(self, prefix, *, out_lines=None, in_lines=None, **kwargs):
        # Branching pattern
        self.in_lines = in_lines or list()
        self.out_lines = out_lines or list()
        super().__init__(prefix, **kwargs)

    @property
    def destination(self):
        """Current list of destinations the mirror currently supports."""
        # Inserted
        if self.inserted and not self.removed:
            return self.in_lines
        # Removed
        elif self.removed and not self.inserted:
            return self.out_lines
        # Unknown
        else:
            return []

    @property
    def branches(self):
        """Return all possible beamlines for mirror destinations."""
        return self.in_lines + self.out_lines

    def check_value(self, pos):
        """Check that our gantry is coupled before state moves."""
        # Check the X gantry
        if self.xgantry.decoupled.get():
            raise PermissionError("Can not move the horizontal gantry is "
                                  "uncoupled")
        # Allow StatePositioner to check the state
        return super().check_value(pos)


class XOffsetMirror(BaseInterface, GroupDevice, LightpathMixin):
    """
    X-ray Offset Mirror.

    1st and 2nd gen Axilon designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Motor components: can read/write positions
    y_up = Cpt(BeckhoffAxisNoOffset, ':MMS:YUP', kind='hinted',
               doc='Yupstream master axis [um]')
    x_up = Cpt(BeckhoffAxisNoOffset, ':MMS:XUP', kind='hinted',
               doc='Xupstream master [um]')
    pitch = Cpt(BeckhoffAxisNoOffset, ':MMS:PITCH', kind='hinted',
                doc='Pitch stepper and piezo axes [urad]')
    bender = Cpt(BeckhoffAxisNoOffset, ':MMS:BENDER', kind='normal',
                 doc='Bender motor [um]')
    y_dwn = Cpt(BeckhoffAxisNoOffset, ':MMS:YDWN', kind='config',
                doc='Ydwnstream slave axis [um]')
    x_dwn = Cpt(BeckhoffAxisNoOffset, ':MMS:XDWN', kind='config',
                doc='Xdwnstream slave axis [um]')

    # Gantry components
    gantry_x = Cpt(PytmcSignal, ':GANTRY_X', io='i', kind='normal',
                   doc='X gantry difference [um]')
    gantry_y = Cpt(PytmcSignal, ':GANTRY_Y', io='i', kind='normal',
                   doc='Y gantry difference [um]')
    couple_y = Cpt(PytmcSignal, ':COUPLE_Y', io='o', kind='config',
                   doc='Couple Y motors [bool]')
    couple_x = Cpt(PytmcSignal, ':COUPLE_X', io='o', kind='config',
                   doc='Couple X motors [bool]')
    decouple_y = Cpt(PytmcSignal, ':DECOUPLE_Y', io='o', kind='config',
                     doc='Decouple Y motors [bool]')
    decouple_x = Cpt(PytmcSignal, ':DECOUPLE_X', io='o', kind='config',
                     doc='Decouple X motors [bool]')
    couple_status_y = Cpt(PytmcSignal, ':ALREADY_COUPLED_Y', io='i',
                          kind='normal')
    couple_status_x = Cpt(PytmcSignal, ':ALREADY_COUPLED_X', io='i',
                          kind='normal')
    # RMS Cpts:
    y_enc_rms = Cpt(PytmcSignal, ':ENC:Y:RMS', io='i', kind='normal',
                    doc='Yup encoder RMS deviation [um]')
    x_enc_rms = Cpt(PytmcSignal, ':ENC:X:RMS', io='i', kind='normal',
                    doc='Xup encoder RMS deviation [um]')
    pitch_enc_rms = Cpt(PytmcSignal, ':ENC:PITCH:RMS', io='i', kind='normal',
                        doc='Pitch encoder RMS deviation [urad]')
    bender_enc_rms = Cpt(PytmcSignal, ':ENC:BENDER:RMS', io='i',
                         kind='normal',
                         doc='Bender encoder RMS deviation [um]')

    # Lightpath config: implement inserted, removed, transmission, subscribe
    # For now, keep it simple. Some mirrors need more than this, but it is
    # sufficient for MR1L0 and MR2L0 for today.

    # We watch the user_readback here, but the name of its component is
    # that of the bare signal (x_up.user_readback -> x_up)
    lightpath_cpts = ['x_up.user_readback', 'y_up.user_readback',
                      'pitch.user_readback']

    def __init__(
        self,
        *args,
        x_ranges: List[List[int]] = [],
        y_ranges: List[List[int]] = [],
        pitch_ranges: List[List[List[int]]] = [],
        **kwargs
    ) -> None:
        # insertion status, [[min_x_out, max_x_out], [min_x_in, max_x_in]]
        self.x_ranges = x_ranges
        # coating status.  (n_coatings * 2) array
        # [ [min_y_coat1, max_y_coat1],
        #   [min_y_coat2, max_y_coat2],
        #   ... ]
        self.y_ranges = y_ranges
        # pitch (output branch) status.
        # (n_coatings * n_destination * 2) array
        # [
        #  [ [min_p_coat1out1, max_p_coat1out1], [coat1out2_ranges], ...],
        #  [ [min_p_coat2out1, max_p_coat2out1], [coat1out2_ranges], ...],
        #  ...
        # ]
        self.pitch_ranges = pitch_ranges
        super().__init__(*args, **kwargs)

    def calc_lightpath_state(
        self,
        x_up: float,
        y_up: float,
        pitch: float
    ) -> LightpathState:
        # all mirrors have roughly the same logic, but some may have
        # relevant information in state-PV's, so argument names may not
        # be the same.
        # here we convert to positional arguments to try and re-use logic
        return self._calc_lightpath_state(x_up, y_up, pitch)

    def _calc_lightpath_state(
        self,
        x_info: float,
        y_info: float,
        pitch_info: float
    ) -> LightpathState:
        """
        Calculate the lightpath-state information by dispatching to
        helper methods.  These methods may change in later subclasses,
        as may the types of the arguments.

        However, the base logic will remain the same.
        (the way we walk the decision tree does not change)

        We assume that in every case, we receive the following info
        - x-position --> insertion status
        - y-position --> coating information
        - pitch      --> output branch

        Roughly speaking the decision tree goes as follows:
        - Determine if mirror is inserted:
            - if removed, beam goes straight through, return
            - if inserted, continue
        - Determine which coating is being used, and use coating to
          determine which set of pitch ranges to use
        - Determine which destination the mirror is delivering beam to
          based on the pitch
        """
        try:
            x_out, x_in = self._get_insertion_state(x_info)

            if x_out:
                return LightpathState(inserted=x_in, removed=x_out,
                                      output={self.output_branches[0]: 1})

            # if in, check coating
            coating_index = self._get_coating_index(y_info)

            out_branch = self._get_output_branch(coating_index, pitch_info)

            # transmission is always 1 if miror is configured properly
            trans = 1

            return LightpathState(
                inserted=x_in,
                removed=x_out,
                output={out_branch: trans}
            )
        except MirrorLogicError as ex:
            # a state for if calculation cannot proceed
            self.log.debug(ex)
            return LightpathState(
                inserted=False,
                removed=False,
                output={self.output_branches[0]: 0}
            )

    def _find_matching_range_indices(
        self,
        ranges: List[List[numeric]],
        value: numeric
    ) -> List[bool]:
        """
        Helper function for finding the range a particular value falls into

        Parameters
        ----------
        ranges : List[List[numeric]]
            A list of ranges.  Each range has a max and min value (exclusive)
        value : numeric
            Value to compare to each range

        Returns
        -------
        List[bool]
            A list of booleans, reporting if the value is in each range
            in ``ranges``
        """
        if len(np.shape(ranges)) < 2:
            raise MirrorLogicError(
                "Provided ranges must be a list of ranges (min, max).  "
                f"Received an array of shape: {np.shape(ranges)}"
            )

        return [limit[0] < value < limit[1] for limit in ranges]

    def _get_insertion_state(self, x: float) -> Tuple[bool, bool]:
        """
        Interpret x-position as inserted or removed, based on ranges
        provided at init.

        Assumes first range is OUT, second range is IN

        Parameters
        ----------
        x : float
            x-position

        Raises
        ------
        MirrorLogicError
            if the provided insertion ranges are malformed (wrong shape)

        Returns
        -------
        is_out, is_in : Tuple[bool, bool]
            tuple of booleans describing the inserted and removed status
        """
        if self.x_ranges == []:
            # default case for always-in mirrors
            return False, True

        if np.shape(self.x_ranges) != (2, 2):
            # improper ranges for insertion, fail
            raise MirrorLogicError(
                'Provided x-ranges are the malformed. '
                f'got: {np.shape(self.x_ranges)}, expected (2,2)')

        ins_bools = self._find_matching_range_indices(self.x_ranges, x)
        return ins_bools[0], ins_bools[1]  # out, in

    def _get_coating_index(self, y: float) -> int:
        """
        Convert y-position to coating index

        Parameters
        ----------
        y : float
            y-position

        Raises
        ------
        MirrorLogicError
            if y is found to be in more than one y-range

        Returns
        -------
        index : int
            The coating state
        """
        if self.y_ranges == []:
            return 1

        y_idxs = self._find_matching_range_indices(self.y_ranges, y)
        valid_y_idx = np.where(y_idxs)[0]
        if len(valid_y_idx) > 1:
            # should only see one valid y-range, coating unknown
            raise MirrorLogicError('only one y-range should be valid')
        elif len(valid_y_idx) == 0:
            # coating state is unknown
            raise MirrorLogicError('Coating state is unknown, mirror '
                                   'is not aligned given provided '
                                   'y-ranges')

        return valid_y_idx[0] + 1

    def _get_output_branch(self, coating_idx: int, pitch: float) -> str:
        """
        get output branch given coating state and pitch

        Parameters
        ----------
        coating_idx : int
            index used to access relevant pitch ranges. First coating
            is 0-indexed

        pitch : float
            pitch of the mirror, will be compared against provided
            pitch ranges

        Raises
        ------
        MirrorLogicError
            if number of valid pitch ranges is not 1.  If no valid
            ranges are found, mirror is not

        Returns
        -------
        output_branch : str
            the name of the current beam destination
        """
        if self.pitch_ranges == []:
            return self.output_branches[0]

        # use coating to pick proper pitch ranges
        # 0 state is unknown, 1 is the first coating.  decrement to get index
        pitch_limit_list = self.pitch_ranges[coating_idx]

        # find indices ranges where pitch is valid
        pitch_idxs = self._find_matching_range_indices(pitch_limit_list, pitch)
        valid_pitch_idx = np.where(pitch_idxs)[0]

        # pitch should only be within one valid range
        if len(valid_pitch_idx) != 1:
            raise MirrorLogicError('only one pitch-range should be valid')

        # index of valid range = index of output_branch + 1
        # assuming first output_branch is through line
        return self.output_branches[valid_pitch_idx[0] + 1]

    # Tab config: show components
    tab_component_names = True

    def format_status_info(self, status_info):
        """
        Override status info handler to render the Hard X-ray Offset Mirror.

        Display homs status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        # happi metadata
        try:
            md = self.root.md
        except AttributeError:
            name = f'{self.prefix}'
        else:
            beamline = get_status_value(md, 'beamline')
            functional_group = get_status_value(md, 'functional_group')
            if functional_group is not None:
                name = f'{self.prefix} ({beamline} {functional_group})'
            else:
                name = f'{self.prefix} ({beamline})'

        x_position = get_status_value(status_info, 'x_up', 'position')
        x_user_setpoint = get_status_value(status_info, 'x_up',
                                           'user_setpoint', 'value')
        x_units = get_status_value(status_info, 'x_up', 'user_setpoint',
                                   'units')
        x_description = get_status_value(status_info, 'x_up', 'description',
                                         'value')

        p_position = get_status_value(status_info, 'pitch', 'position')
        p_user_setpoint = get_status_value(status_info, 'pitch',
                                           'user_setpoint', 'value')
        p_units = get_status_value(status_info, 'pitch', 'user_setpoint',
                                   'units')
        p_description = get_status_value(status_info, 'pitch', 'description',
                                         'value')
        p_enc_rms = get_status_value(status_info, 'pitch_enc_rms', 'value')

        return f"""\
{name}
------
x_up: ({self.x_up.prefix})
------
    position: {x_position}
    user_setpoint: {x_user_setpoint} [{x_units}]
    description: {x_description}
------
pitch: ({self.pitch.prefix})
------
    position: {p_position}
    user_setpoint: {p_user_setpoint} [{p_units}]
    description: {p_description}
    pitch_enc_rms: {p_enc_rms}
"""


class XOffsetMirrorRTDs(XOffsetMirror):
    """
    X-ray Offset Mirror.

    1st and 2nd gen Axilon designs with LCLS-II Beckhoff motion architecture.

    With 3 RTD sensors installed.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # RTD Cpts:
    rtd_1 = Cpt(PytmcSignal, ':RTD:1', io='i', kind='normal')
    rtd_2 = Cpt(PytmcSignal, ':RTD:2', io='i', kind='normal')
    rtd_3 = Cpt(PytmcSignal, ':RTD:3', io='i', kind='normal')


class XOffsetMirrorBend(XOffsetMirror):
    """
    X-ray Offset Mirror with 2 bender acutators.

    1st and 2nd gen Axilon designs with LCLS-II Beckhoff motion architecture.

    Currently (09/28/2022) services: mr1k1

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Do a dumb thing and kill inherited single bender
    bender = None
    bender_enc_rms = None

    # Motor components: can read/write positions
    bender_us = Cpt(BeckhoffAxisNoOffset, ':MMS:US', kind='hinted')
    bender_ds = Cpt(BeckhoffAxisNoOffset, ':MMS:DS', kind='hinted')

    # RMS Cpts:
    bender_us_enc_rms = Cpt(PytmcSignal, ':ENC:US:RMS', io='i',
                            kind='normal')
    bender_ds_enc_rms = Cpt(PytmcSignal, ':ENC:DS:RMS', io='i',
                            kind='normal')

    # Bender RTD Cpts:
    us_rtd = Cpt(EpicsSignalRO, ':RTD:US:1_RBV', kind='normal')
    ds_rtd = Cpt(EpicsSignalRO, ':RTD:DS:1_RBV', kind='normal')

    # Tab config: show components
    tab_component_names = True

    def calc_lightpath_state(
        self,
        x_up: float,
        y_up: float,
        pitch: float
    ) -> LightpathState:
        """
        Special lightpath calculation for mr1k1_bend, which only
        depends on y-range for insertion, rather than x-range

        Parameters
        ----------
        x_up : float
            x position, unused
        y_up : float
            y position, used to determine insertion
        pitch : float
            pitch position, unused

        Returns
        -------
        LightpathState
            current lightpath state of the device
        """
        try:
            if np.shape(self.y_ranges) != (2, 2):
                # improper ranges for insertion, fail
                raise MirrorLogicError(
                    'Provided x-ranges are the malformed. '
                    f'got: {np.shape(self.x_ranges)}, expected (2,2)')

            x_out, x_in = self._find_matching_range_indices(self.y_ranges,
                                                            y_up)

            if x_in and not x_out:
                out_branch = self.output_branches[1]
            else:
                # default to pass through.  in/out state will block
                # if state is bad.
                out_branch = self.output_branches[0]

            return LightpathState(
                inserted=x_in,
                removed=x_out,
                output={out_branch: 1}
            )
        except MirrorLogicError as ex:
            self.log.debug(ex)
            return LightpathState(
                inserted=False,
                removed=False,
                output={self.output_branches[0]: 0}
            )


# Maintain backward compatibility
XOffsetMirror2 = XOffsetMirrorBend


class XOffsetMirrorSwitch(XOffsetMirror):
    """
    X-ray Offset Mirror with Yleft/Yright

    1st and 2nd gen Axilon designs with LCLS-II Beckhoff motion architecture.

    currently (09/28/2022) services: mr1k2

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Do a dumb thing and kill inherited/unused components
    y_up = None
    y_dwn = None
    bender = None
    bender_enc_rms = None

    # Motor components: can read/write positions
    y_left = Cpt(BeckhoffAxisNoOffset, ':MMS:YLEFT', kind='hinted',
                 doc='Yleft master axis [um]')
    y_right = Cpt(BeckhoffAxisNoOffset, ':MMS:YRIGHT', kind='config',
                  doc='Yright slave axis [um]')

    # Tab config: show components
    tab_component_names = True

    # Update for missing components
    lightpath_cpts = ['x_up.user_readback', 'pitch.user_readback']

    def calc_lightpath_state(
        self,
        x_up: float,
        pitch: float
    ) -> LightpathState:
        # currently always in, no switching
        return LightpathState(
            inserted=True, removed=False, output={self.output_branches[0]: 1}
        )


class KBOMirror(BaseInterface, GroupDevice, LightpathMixin):
    """
    Kirkpatrick-Baez Mirror with Bender Axes.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Motor components: can read/write positions
    x = Cpt(BeckhoffAxisNoOffset, ':MMS:X', kind='hinted')
    y = Cpt(BeckhoffAxisNoOffset, ':MMS:Y', kind='hinted')
    pitch = Cpt(BeckhoffAxisNoOffset, ':MMS:PITCH', kind='hinted')
    bender_us = Cpt(BeckhoffAxisNoOffset, ':MMS:BEND:US', kind='hinted')
    bender_ds = Cpt(BeckhoffAxisNoOffset, ':MMS:BEND:DS', kind='hinted')

    # RMS Cpts:
    x_enc_rms = Cpt(PytmcSignal, ':ENC:X:RMS', io='i', kind='normal')
    y_enc_rms = Cpt(PytmcSignal, ':ENC:Y:RMS', io='i', kind='normal')
    pitch_enc_rms = Cpt(PytmcSignal, ':ENC:PITCH:RMS', io='i', kind='normal')
    bender_us_enc_rms = Cpt(PytmcSignal, ':ENC:BEND:US:RMS', io='i',
                            kind='normal')
    bender_ds_enc_rms = Cpt(PytmcSignal, ':ENC:BEND:DS:RMS', io='i',
                            kind='normal')

    # Bender RTD Cpts:
    us_rtd = Cpt(EpicsSignalRO, ':RTD:BEND:US:1_RBV', kind='normal')
    ds_rtd = Cpt(EpicsSignalRO, ':RTD:BEND:DS:1_RBV', kind='normal')

    lightpath_cpts = ['x.user_readback', 'y.user_readback']
    # Lightpath config: implement inserted, removed, transmission, subscribe

    def calc_lightpath_state(
        self,
        x: float,
        y: float
    ) -> LightpathState:
        # TODO: get real logic
        return LightpathState(
            inserted=True, removed=False, output={self.output_branches[0]: 1}
        )

    # Tab config: show components
    tab_component_names = True

    def format_status_info(self, status_info):
        """
        Override status info handler to render the `KBOMirror`.

        Display `KBOMirror` status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        # happi metadata
        try:
            md = self.root.md
        except AttributeError:
            name = f'{self.prefix}'
        else:
            beamline = get_status_value(md, 'beamline')
            functional_group = get_status_value(md, 'functional_group')
            if functional_group is not None:
                name = f'{self.prefix} ({beamline} {functional_group})'
            else:
                name = f'{self.prefix} ({beamline})'

        x_position = get_status_value(status_info, 'x', 'position')
        x_user_setpoint = get_status_value(status_info, 'x',
                                           'user_setpoint', 'value')
        x_units = get_status_value(status_info, 'x', 'user_setpoint',
                                   'units')
        x_description = get_status_value(status_info, 'x', 'description',
                                         'value')
        y_position = get_status_value(status_info, 'y', 'position')
        y_user_setpoint = get_status_value(status_info, 'y',
                                           'user_setpoint', 'value')
        y_units = get_status_value(status_info, 'y', 'user_setpoint',
                                   'units')
        y_description = get_status_value(status_info, 'y', 'description',
                                         'value')
        p_position = get_status_value(status_info, 'pitch', 'position')
        p_user_setpoint = get_status_value(status_info, 'pitch',
                                           'user_setpoint', 'value')
        p_units = get_status_value(status_info, 'pitch', 'user_setpoint',
                                   'units')
        p_description = get_status_value(status_info, 'pitch', 'description',
                                         'value')
        p_enc_rms = get_status_value(status_info, 'pitch_enc_rms', 'value')
        b_us_position = get_status_value(status_info, 'bender_us', 'position')
        b_us_setpoint = get_status_value(status_info, 'bender_us',
                                         'user_setpoint', 'value')
        b_us_units = get_status_value(status_info, 'bender_us',
                                      'user_setpoint', 'units')
        b_us_description = get_status_value(status_info, 'bender_us',
                                            'description', 'value')
        b_us_enc_rms = get_status_value(status_info, 'bender_us_enc_rms',
                                        'value')
        b_ds_position = get_status_value(status_info, 'bender_ds', 'position')
        b_ds_setpoint = get_status_value(status_info, 'bender_ds',
                                         'user_setpoint', 'value')
        b_ds_units = get_status_value(status_info, 'bender_ds',
                                      'user_setpoint', 'units')
        b_ds_description = get_status_value(status_info, 'bender_ds',
                                            'description', 'value')
        b_ds_enc_rms = get_status_value(status_info, 'bender_ds_enc_rms',
                                        'value')
        return f"""\
{name}
------
x_up: ({self.x.prefix})
------
    position: {x_position}
    user_setpoint: {x_user_setpoint} [{x_units}]
    description: {x_description}
------
y_up: ({self.y.prefix})
------
    position: {y_position}
    user_setpoint: {y_user_setpoint} [{y_units}]
    description: {y_description}
------
pitch: ({self.pitch.prefix})
------
    position: {p_position}
    user_setpoint: {p_user_setpoint} [{p_units}]
    description: {p_description}
    pitch_enc_rms: {p_enc_rms}
---------
bender_us ({self.bender_us.prefix})
---------
    position {b_us_position}
    user_setpoint: {b_us_setpoint} [{b_us_units}]
    description: {b_us_description}
    bender_us_enc_rms: {b_us_enc_rms}
---------
bender_ds ({self.bender_ds.prefix})
---------
    position: {b_ds_position}
    user_setpoint: {b_ds_setpoint} [{b_ds_units}]
    description: {b_ds_description}
    bender_ds_enc_rms: {b_ds_enc_rms}
"""


class KBOMirrorHE(KBOMirror):
    """
    Kirkpatrick-Baez Mirror with Bender Axes and Cooling.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # Cooling water flow and pressure sensors
    cool_flow1 = Cpt(EpicsSignalRO, ':FLOW:1_RBV', kind='normal')
    cool_flow2 = Cpt(EpicsSignalRO, ':FLOW:2_RBV', kind='normal')
    cool_press = Cpt(EpicsSignalRO, ':PRESS:1_RBV', kind='normal')

    # Tab config: show components
    tab_component_names = True


class FFMirror(BaseInterface, GroupDevice, LightpathMixin):
    """
    Fixed Focus Kirkpatrick-Baez Mirror.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Motor components: can read/write positions
    x = Cpt(BeckhoffAxisNoOffset, ':MMS:X', kind='hinted')
    y = Cpt(BeckhoffAxisNoOffset, ':MMS:Y', kind='hinted')
    pitch = Cpt(BeckhoffAxisNoOffset, ':MMS:PITCH', kind='hinted')

    # RMS Cpts:
    x_enc_rms = Cpt(PytmcSignal, ':ENC:X:RMS', io='i', kind='normal')
    y_enc_rms = Cpt(PytmcSignal, ':ENC:Y:RMS', io='i', kind='normal')
    pitch_enc_rms = Cpt(PytmcSignal, ':ENC:PITCH:RMS', io='i', kind='normal')

    # Lightpath config: implement inserted, removed, transmission, subscribe
    lightpath_cpts = ['x.user_readback', 'y.user_readback']

    # Lightpath config: implement inserted, removed, transmission, subscribe
    def calc_lightpath_state(
        self,
        x: float,
        y: float
    ) -> LightpathState:
        # TODO: get real logic
        return LightpathState(
            inserted=True, removed=False, output={self.output_branches[0]: 1}
        )

    # Tab config: show components
    tab_component_names = True

    def format_status_info(self, status_info):
        """
        Override status info handler to render the `FFMirror`.

        Display `FFMirror` status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        # happi metadata
        try:
            md = self.root.md
        except AttributeError:
            name = f'{self.prefix}'
        else:
            beamline = get_status_value(md, 'beamline')
            functional_group = get_status_value(md, 'functional_group')
            if functional_group is not None:
                name = f'{self.prefix} ({beamline} {functional_group})'
            else:
                name = f'{self.prefix} ({beamline})'

        x_position = get_status_value(status_info, 'x', 'position')
        x_user_setpoint = get_status_value(status_info, 'x',
                                           'user_setpoint', 'value')
        x_units = get_status_value(status_info, 'x', 'user_setpoint',
                                   'units')
        x_description = get_status_value(status_info, 'x', 'description',
                                         'value')

        p_position = get_status_value(status_info, 'pitch', 'position')
        p_user_setpoint = get_status_value(status_info, 'pitch',
                                           'user_setpoint', 'value')
        p_units = get_status_value(status_info, 'pitch', 'user_setpoint',
                                   'units')
        p_description = get_status_value(status_info, 'pitch', 'description',
                                         'value')
        p_enc_rms = get_status_value(status_info, 'pitch_enc_rms', 'value')

        return f"""\
{name}
------
x_up: ({self.x.prefix})
------
    position: {x_position}
    user_setpoint: {x_user_setpoint} [{x_units}]
    description: {x_description}
------
pitch: ({self.pitch.prefix})
------
    position: {p_position}
    user_setpoint: {p_user_setpoint} [{p_units}]
    description: {p_description}
    pitch_enc_rms: {p_enc_rms}
"""


@reorder_components(
    end_with=['x_enc_rms', 'y_enc_rms', 'z_enc_rms', 'pitch_enc_rms']
)
class FFMirrorZ(FFMirror):
    """
    Fixed Focus Kirkpatrick-Baez Mirror with Z axis.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # Motor components: can read/write positions
    z = Cpt(BeckhoffAxisNoOffset, ':MMS:Z', kind='hinted')

    # RMS Cpts:
    z_enc_rms = Cpt(PytmcSignal, ':ENC:Z:RMS', io='i', kind='normal')


class TwinCATMirrorStripe(TwinCATStatePMPS):
    """
    Subclass of TwinCATStatePMPS for the mirror coatings.

    Unless most TwinCATStatePMPS, we have:
    - Only in_states
    - No in_states block the beam

    We also clear the states_list and set _in_if_not_out to True
    to automatically pick up the coatings from each mirror enum.
    """
    states_list = []
    in_states = []
    out_states = []
    _in_if_not_out = True
    config = UpCpt(state_count=2)

    @property
    def transmission(self):
        """The mirror coating never blocks the beam."""
        return 1


@reorder_components(
    end_with=[
        'coating', 'x', 'y', 'pitch', 'bender_us', 'bender_ds',
        'x_enc_rms', 'y_enc_rms', 'pitch_enc_rms', 'bender_us_enc_rms',
        'bender_ds_enc_rms', 'us_rtd', 'ds_rtd'
    ]
)
class KBOMirrorStates(KBOMirror):
    """
    Kirkpatrick-Baez Mirror with Bender Axes and Coating States.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    coating = Cpt(TwinCATMirrorStripe, ':COATING:STATE', kind='hinted',
                  doc='Control of the coating states via saved positions.')

    # Tab config: show components
    tab_component_names = True


@reorder_components(
    end_with=[
        'coating', 'x', 'y', 'pitch', 'bender_us', 'bender_ds',
        'x_enc_rms', 'y_enc_rms', 'pitch_enc_rms', 'bender_us_enc_rms',
        'bender_ds_enc_rms', 'us_rtd', 'ds_rtd', 'cool_flow1',
        'cool_flow2', 'cool_press'
    ]
)
class KBOMirrorHEStates(KBOMirrorHE):
    """
    Kirkpatrick-Baez Mirror with Bender Axes and Cooling and Coating States.

    1st gen Toyama designs with LCLS-II Beckhoff motion architecture.

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    coating = Cpt(TwinCATMirrorStripe, ':COATING:STATE', kind='hinted',
                  doc='Control of the coating states via saved positions.')
    # Tab config: show components
    tab_component_names = True


class CoatingState(Device):
    """
    Extra parent class to put "coating" as the first device in order.

    This makes it appear at the top of the screen in typhos.
    """
    coating = Cpt(TwinCATMirrorStripe, ':COATING:STATE', kind='hinted',
                  doc='Control of the coating states via saved positions.')


class XOffsetMirrorState(XOffsetMirror, CoatingState):
    """
    X-ray Offset Mirror with Yleft/Yright

    1st and 2nd gen Axilon designs with LCLS-II Beckhoff motion architecture.

    With Coating State selection implemented

    Parameters
    ----------
    prefix : str
        Base PV for the mirror.

    name : str
        Alias for the device.
    """
    # UI representation
    _icon = 'fa.minus-square'

    lightpath_cpts = ['x_up.user_readback', 'coating.state',
                      'pitch.user_readback']

    def _get_coating_index(self, y: int) -> int:
        """
        return coating index, essentially just passing through the
        provided argument decremented by one.  (0 is unknown)

        Parameters
        ----------
        y : int
            coating state

        Returns
        -------
        int
            coating index

        Raises
        ------
        MirrorLogicError
            if mirror coating state is not valid or unknown
        """
        if y < 1:
            raise MirrorLogicError('coating state not valid or unknown')
        return y - 1

    def calc_lightpath_state(
        self,
        x_up: float,
        coating_state: int,
        pitch: float
    ) -> LightpathState:
        return self._calc_lightpath_state(x_up, coating_state, pitch)


class MirrorInsertState(TwinCATStatePMPS):
    """
    A state positioner with two states (3 including Unknown) representing
    insertion state of mirror
    """
    _in_if_not_out = True

    config = UpCpt(state_count=2)


class XOffsetMirrorXYState(XOffsetMirrorState):
    """
    X-ray Offset Mirror with state positioners for both coating (y)
    and insertion (x).  Thus, lightpath state calcs only require pitch
    ranges.

    Currently (09/28/2022) services: mr1l3, mr1l4.

    Parameters
    ----------
    pitch_thresholds
    """

    insertion = Cpt(MirrorInsertState, ':MMS:XUP:STATE',
                    doc='Control of mirror insertion via saved positions')

    lightpath_cpts = ['insertion.state', 'coating.state',
                      'pitch.user_readback']

    def _get_insertion_state(
        self,
        insertion_state: int
    ) -> Tuple[bool, bool]:
        """
        return insertion state, given presence of state PV's

        Parameters
        ----------
        insertion_state : int
            insertion state (0: unknown, 1: out, 2: in)

        Returns
        -------
        Tuple[bool, bool]
            is_out, is_in

        Raises
        ------
        MirrorLogicError
            if insertion state is not initialized.  re-calculation
            will be scheduled.
        """
        if not self.insertion._state_initialized:
            self.log.debug('insertion state not initialized, '
                           'scheduling lightpath calcs for later')

            schedule_task(self._calc_cache_lightpath_state, delay=2.0)
            raise MirrorLogicError('insertion state not initialized')

        x_in = self.insertion.check_inserted(insertion_state)
        x_out = self.insertion.check_removed(insertion_state)

        return x_out, x_in

    def calc_lightpath_state(
        self,
        insertion_state: int,
        coating_state: int,
        pitch: float
    ) -> LightpathState:
        return super()._calc_lightpath_state(insertion_state,
                                             coating_state,
                                             pitch)


class OpticsPitchNotepad(BaseInterface, Device):
    """
    class for storing pitch positions based on state

    This provides an interface to the optics notepad IOC where
    the X-Ray beam delivery team can store
    pitch set points based on coating state.

    """
    mr1l0_pitch_b4c = Cpt(EpicsSignal, 'MR1L0:PITCH:Coating1')
    mr1l0_pitch_ni = Cpt(EpicsSignal, 'MR1L0:PITCH:Coating2')

    mr2l0_pitch_b4c = Cpt(EpicsSignal, 'MR2L0:PITCH:Coating1')
    mr2l0_pitch_ni = Cpt(EpicsSignal, 'MR2L0:PITCH:Coating2')

    mr1l4_pitch_mec_sic = Cpt(EpicsSignal, 'MR1L4:PITCH:MEC:Coating1')
    mr1l4_pitch_mec_w = Cpt(EpicsSignal, 'MR1L4:PITCH:MEC:Coating2')

    mr1l4_pitch_mfx_sic = Cpt(EpicsSignal, 'MR1L4:PITCH:MFX:Coating1')
    mr1l4_pitch_mfx_w = Cpt(EpicsSignal, 'MR1L4:PITCH:MFX:Coating2')

    mr1l3_pitch_sic = Cpt(EpicsSignal, 'MR1L3:PITCH:Coating1')
    mr1l3_pitch_w = Cpt(EpicsSignal, 'MR1L3:PITCH:Coating2')

    mr2l3_pitch_sic = Cpt(EpicsSignal, 'MR2L3:PITCH:Coating1')
    mr2l3_pitch_w = Cpt(EpicsSignal, 'MR2L3:PITCH:Coating2')
