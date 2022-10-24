"""
Standard classes for LCLS Gate Valves.
"""
import logging
from enum import IntEnum

from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV

from .interface import LightpathMixin
from .stopper import PPSStopper, Stopper  # noqa import PPS for backcompat

logger = logging.getLogger(__name__)


class Commands(IntEnum):
    """Command aliases for opening and closing valves."""
    close_valve = 0
    open_valve = 1


class InterlockError(PermissionError):
    """Error when request is blocked by interlock logic."""
    pass


class GateValve(Stopper):
    """
    Basic Vacuum Valve.

    This inherits directly from `.Stopper` but adds additional logic to check
    the state of the interlock before requesting motion. This is not a safety
    feature, just a notice to the operator.

    This class has been replaced by `VGCLegacy` but has not been removed as
    some elements still need to be carried over.
    """

    # Limit based states
    open_limit = Cpt(
        EpicsSignalRO,
        ':OPN_DI',
        kind='normal'
    )
    closed_limit = Cpt(
        EpicsSignalRO,
        ':CLS_DI',
        kind='normal'
    )

    # Commands and Interlock information
    command = Cpt(
        EpicsSignal,
        ':OPN_SW',
        kind='omitted'
    )
    commands = Commands
    interlock = Cpt(
        EpicsSignalRO,
        ':OPN_OK',
        kind='normal'
     )

    # QIcon for UX
    _icon = 'fa.hourglass'

    tab_whitelist = ['interlocked']

    def check_value(self, value):
        """Check when removing GateValve interlock is off."""
        value = super().check_value(value)
        if value == self.states_enum.OUT and self.interlocked:
            raise InterlockError('Valve is currently forced closed')
        return value

    @property
    def interlocked(self):
        """
        Whether the valve's interlock is active, preventing the valve from
        opening.
        """
        return not bool(self.interlock.get())


class ValveBase(Device):
    """
    Base class for valves.

    Valves are normally closed by default.

    Newer class. This and below are still missing some functionality.
    Still need to work out replacement of old classes.

    This corresponds to ST_ValveBase in the lcls-twincat-vacuum library.
    PVs that are omitted in VCGLegacy are instead put in the VVC class.
    """

    valve_position = Cpt(
        EpicsSignalRO,
        ':POS_STATE_RBV',
        kind='hinted',
        doc='Ex: OPEN, CLOSED, MOVING, INVALID, OPEN_F'
    )
    open_command = Cpt(
        EpicsSignalWithRBV,
        ':OPN_SW',
        kind='normal',
        doc='Epics command to Open valve'
    )
    interlock_ok = Cpt(
        EpicsSignalRO,
        ':OPN_OK_RBV',
        kind='normal',
        doc='Valve is OK to Open interlock '
    )
    open_do = Cpt(
        EpicsSignalRO,
        ':OPN_DO_RBV',
        kind='normal',
        doc='PLC Output to Open valve, 1 means 24V on command cable'
    )
    error_reset = Cpt(
        EpicsSignalWithRBV,
        ':ALM_RST',
        kind='normal',
        doc='Reset Error state to valid by toggling this'
    )


class VVC(ValveBase):
    """
    VVC = Vent Valve, Controlled.

    This corresponds to ST_ValveBase in the lcls-twincat-vacuum library.
    It contains PVs missing for VGCLegacy.

    All new controlled valve classes should inherit from VVC.
    """
    override_status = Cpt(
        EpicsSignalRO,
        ':OVRD_ON_RBV',
        kind='omitted',
        doc='Epics Readback on Override mode'
    )
    override_force_open = Cpt(
        EpicsSignalWithRBV,
        ':FORCE_OPN',
        kind='omitted',
        doc=('Epics Command to force open the valve in'
             'override mode')
    )


class VGCLegacy(ValveBase):
    """
    Class for Basic Vacuum Valve.

    Replaces the `GateValve` class.
    This does not correspond to any TwinCAT libraries.
    """

    open_limit = Cpt(
        EpicsSignalRO,
        ':OPN_DI_RBV',
        kind='hinted',
        doc='Open limit switch digital input'
    )
    closed_limit = Cpt(
        EpicsSignalRO,
        ':CLS_DI_RBV',
        kind='hinted',
        doc='Closed limit switch digital input'
    )


class VRC(VVC, LightpathMixin):
    """
    VRC = Valve with Readback and Control

    This is the standard normally-closed valve class.
    It corresponds with ST_VRC in the lcls-twincat-vacuum library,
    though it also adds some PVs from ST_ValveBase.

    This class does not contain detailed interlocking information,
    rather it only includes whether or not an interlock is present.
    """

    # Configuration for lightpath
    lightpath_cpts = ['open_limit', 'closed_limit']
    _icon = 'fa.hourglass'

    state = Cpt(
        EpicsSignalRO,
        ':STATE_RBV',
        kind='normal',
        doc='Valve state'
    )
    open_limit = Cpt(
        EpicsSignalRO,
        ':OPN_DI_RBV',
        kind='hinted',
        doc='Open limit switch digital input'
    )
    closed_limit = Cpt(
        EpicsSignalRO,
        ':CLS_DI_RBV',
        kind='hinted',
        doc='Closed limit switch digital input'
    )

    def calc_lightpath_state(
        self, open_limit: int, closed_limit: int
    ) -> LightpathState:
        """Callback for updating inserted/removed for lightpath."""

        self._inserted = bool(closed_limit)
        self._removed = bool(open_limit)

        trans = 0.0 if self._inserted else 1.0

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: trans}
        )


class VRCClsLS(VVC):
    """
    Valve with Readback and Control and only a Closed Limit Switch.

    This class is just VRC but without open_limit.
    """

    state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='normal', doc='Valve state')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI_RBV', kind='hinted',
                       doc='Closed limit switch digital input')


class VGC(VRC):
    """
    VGC = Vacuum Gate valve, Controlled

    This is the gate valve class with detailed interlocking information
    available. These valves are typically along the beam path and are
    prevented from opening when the pressure differential is too great.

    These are always normally closed valves, meaning that they are
    always safe to close (in terms of vacuum) and that turning the PLC
    off will cause them to close immediately.

    This corresponds with ST_VGC in the lcls-twincat-vacuum library.
    """
    diff_press_ok = Cpt(
        EpicsSignalRO,
        ':DP_OK_RBV',
        kind='normal',
        doc='Differential pressure interlock ok'
    )
    ext_ilk_ok = Cpt(
        EpicsSignalRO,
        ':EXT_ILK_OK_RBV',
        kind='normal',
        doc='External interlock ok'
    )
    at_vac_setpoint = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_SP',
        kind='config',
        doc='AT VAC Set point value'
    )
    setpoint_hysterisis = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_HYS',
        kind='config',
        doc='AT VAC Hysteresis'
    )
    at_vac = Cpt(
        EpicsSignalRO,
        ':AT_VAC_RBV',
        kind='normal',
        doc='at vacuum setpoint is reached'
    )
    error = Cpt(
        EpicsSignalRO,
        ':ERROR_RBV',
        kind='normal',
        doc='Error Present'
    )
    mps_state = Cpt(
        EpicsSignalRO,
        ':MPS_FAULT_OK_RBV',
        kind='omitted',
        doc=('individual valve MPS state for debugging')
    )
    interlock_device_upstream = Cpt(
        EpicsSignalRO,
        ':ILK_DEVICE_US_RBV',
        kind='config',
        string=True,
        doc='Upstream vacuum device used for'
            'interlocking this valve'
    )
    interlock_device_downstream = Cpt(
        EpicsSignalRO,
        ':ILK_DEVICE_DS_RBV',
        kind='config',
        string=True,
        doc='Downstream vacuum device used for'
            'interlocking this valve'
    )


class VGC_2S(VRC):
    """
    VGC_2S = Vacuum Gate valve, Controlled, with 2 Setpoints.

    This is the class for VGC elements that have different interlock setpoints
    for the upstream and downstream gauges respectively.

    This corresponds with ST_VGC_2S in the lcls-twincat-vacuum library.
    """
    diff_press_ok = Cpt(
        EpicsSignalRO,
        ':DP_OK_RBV',
        kind='normal',
        doc='Differential pressure interlock ok'
    )
    ext_ilk_ok = Cpt(
        EpicsSignalRO,
        ':EXT_ILK_OK_RBV',
        kind='normal',
        doc='External interlock ok'
    )
    at_vac_setpoint_us = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_SP',
        kind='config',
        doc='AT VAC Set point value '
            'for the upstream gauge'
    )
    setpoint_hysterisis_us = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_HYS',
        kind='config',
        doc='AT VAC Hysteresis for '
            'the upstream setpoint'
    )
    at_vac_setpoint_ds = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_SP_DS',
        kind='config',
        doc='AT VAC Set point value '
            'for the downstream gauge'
    )
    setpoint_hysterisis_ds = Cpt(
        EpicsSignalWithRBV,
        ':AT_VAC_HYS_DS',
        kind='config',
        doc='AT VAC Hysteresis for '
            'the downstream setpoint'
    )
    at_vac = Cpt(
        EpicsSignalRO,
        ':AT_VAC_RBV',
        kind='normal',
        doc='at vacuum setpoint is reached'
    )
    error = Cpt(
        EpicsSignalRO,
        ':ERROR_RBV',
        kind='normal',
        doc='Error Present'
    )
    mps_state = Cpt(
        EpicsSignalRO,
        ':MPS_FAULT_OK_RBV',
        kind='omitted',
        doc=('individual valve MPS state for debugging')
    )
    interlock_device_upstream = Cpt(
        EpicsSignalRO,
        ':ILK_DEVICE_US_RBV',
        kind='config',
        string=True,
        doc='Upstream vacuum device used for'
            'interlocking this valve'
    )
    interlock_device_downstream = Cpt(
        EpicsSignalRO,
        ':ILK_DEVICE_DS_RBV',
        kind='config',
        string=True,
        doc='Downstream vacuum device used for'
            'interlocking this valve'
    )


class VFS(LightpathMixin):
    """
    VFS = Fast Shutter Valve

    This valve is typically used to protect sensitive beamline components
    from bad vacuum events that would otherwise damage them. It has an
    especially fast response time compared to other vacuum system elements.

    This corresponds with ST_VFS in the lcls-twincat-vacuum library,
    but rather than inherit from other classes it includes repeated
    elements from ST_ValveBase.
    """

    # Configuration for lightpath
    lightpath_cpts = ['position_open', 'position_close']
    _icon = 'fa.shield'

    valve_position = Cpt(
        EpicsSignalRO,
        ':POS_STATE_RBV',
        kind='hinted',
        doc='Ex: OPEN, CLOSED, MOVING, INVALID, OPEN_F'
    )
    vfs_state = Cpt(
        EpicsSignalRO,
        ':STATE_RBV',
        kind='hinted',
        doc='Fast Shutter Current State'
    )
    request_close = Cpt(
        EpicsSignalWithRBV,
        ':CLS_SW',
        kind='normal',
        doc=('Request Fast Shutter to Close. When both close'
             'and open are requested, VFS will close.')
    )
    request_open = Cpt(
        EpicsSignalWithRBV,
        ':OPN_SW',
        kind='normal',
        doc=('Request Fast Shutter to Open. Requires a rising'
             'EPICS signal to open. When both close and'
             'open are requested, VFS will close.')
    )
    reset_vacuum_fault = Cpt(
        EpicsSignalWithRBV,
        ':ALM_RST',
        kind='normal',
        doc=('Reset Fast Shutter Vacuum Faults: fast'
             'sensor triggered, fast sensor turned off.'
             'To open VFS, this needs to be reset to TRUE'
             'after a vacuum event.')
    )
    override_mode = Cpt(
        EpicsSignalWithRBV,
        ':OVRD_ON',
        kind='normal',
        doc='Epics Command to set Override mode'
    )
    override_force_open = Cpt(
        EpicsSignalWithRBV,
        ':FORCE_OPN',
        kind='normal',
        doc=('Epics Command to force open'
             'the valve in override mode')
    )
    gfs_name = Cpt(
        EpicsSignalRO,
        ':GFS_RBV',
        kind='normal',
        string=True,
        doc='Gauge Fast Sensor Name'
    )
    gfs_trigger = Cpt(
        EpicsSignalRO,
        ':TRIG_RBV',
        kind='normal',
        doc='Gauge Fast Sensor Input Trigger'
    )
    position_close = Cpt(
        EpicsSignalRO,
        ':CLS_DI_RBV',
        kind='normal',
        doc='Fast Shutter Closed Valve Position'
    )
    position_open = Cpt(
        EpicsSignalRO,
        ':OPN_DI_RBV',
        kind='normal',
        doc='Fast Shutter Open Valve Position'
    )
    vac_fault_ok = Cpt(
        EpicsSignalRO,
        ':VAC_FAULT_OK_RBV',
        kind='normal',
        doc=('Fast Shutter Vacuum Fault OK Readback')
    )
    mps_ok = Cpt(
        EpicsSignalRO,
        ':MPS_FAULT_OK_RBV',
        kind='normal',
        doc='Fast Shutter Fast Fault Output OK'
    )
    veto_device = Cpt(
        EpicsSignalRO,
        ':VETO_DEVICE_RBV',
        kind='normal',
        string=True,
        doc='Name of device that can veto this VFS'
    )

    def calc_lightpath_state(self, position_open: int, position_close: int):
        """Callback for updating inserted/removed for lightpath."""

        self._inserted = bool(position_close)
        self._removed = bool(position_open)

        trans = 0.0 if self._inserted else 1.0

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: trans}
        )


class VVCNO(Device):
    """
    VVCNO = Vent Valve, Controlled, Normally Open.

    This is the class for valves that default to the "open" state rather than
    the "closed" state.

    This corresponds with ST_VCCNO in the lcls-twincat-vacuum library,
    though I suspect this is a typo and the file should have been ST_VVCNO.

    This correctly does not inherit from the other classes because the
    corresponding library elements also do not inherit from the other
    classes.
    """
    close_command = Cpt(
        EpicsSignalWithRBV,
        ':CLS_SW',
        kind='normal',
        doc='Epics command to close valve'
    )
    override_force_close = Cpt(
        EpicsSignalWithRBV,
        ':FORCE_CLS',
        kind='omitted',
        doc=('Epics Command for close the valve in override '
             'mode')
    )
    override_on = Cpt(
        EpicsSignalWithRBV,
        ':OVRD_ON',
        kind='omitted',
        doc='Epics Command to set/reset Override mode'
    )
    close_ok = Cpt(
        EpicsSignalRO,
        ':CLS_OK_RBV',
        kind='normal',
        doc='used for normally open valves'
    )
    close_do = Cpt(
        EpicsSignalRO,
        ':CLS_DO_RBV',
        kind='normal',
        doc='PLC Output to close valve'
    )

    @property
    def close_override(self):
        """
        Fixes potential API breaks with old name
        """
        return self.override_force_close


class VRCNO(VVCNO, LightpathMixin):
    """
    VRCNO = Valve with Readback and Control, Normally Open

    This is a valve that defaults to the "open" state and includes
    controllable elements.

    It corresponds with ST_VRC_NO in the lcls-twincat-vacuum library,
    but it also includes elements defined in ST_ValveBase, and it
    doesn't use all of the PVs defined in the struct.
    """

    # Configuration for lightpath
    lightpath_cpts = ['open_limit', 'closed_limit']
    _icon = 'fa.hourglass'

    state = Cpt(
        EpicsSignalRO,
        ':STATE_RBV',
        kind='normal',
        doc='Valve state'
    )

    error_reset = Cpt(
        EpicsSignalWithRBV,
        ':ALM_RST',
        kind='normal',
        doc='Reset Error state to valid by toggling this'
    )
    open_limit = Cpt(
        EpicsSignalRO,
        ':OPN_DI_RBV',
        kind='hinted',
        doc='Open limit switch digital input'
    )
    closed_limit = Cpt(
        EpicsSignalRO,
        ':CLS_DI_RBV',
        kind='hinted',
        doc='Closed limit switch digital input'
    )

    def calc_lightpath_state(self, open_limit: int, closed_limit: int):
        """Callback for updating inserted/removed for lightpath."""

        self._inserted = bool(closed_limit)
        self._removed = bool(open_limit)

        trans = 0.0 if self._inserted else 1.0

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: trans}
        )


class VRCDA(VRC, VRCNO):
    """
    VRCDA = Valve with Readback and Control, Dual Acting

    This is a valve that has no default state. It will maintain its current
    state until asked to change it, and it can be interlocked in either
    direction to prevent opening and to prevent closing.

    This corresponds to ST_VRC_NO in the lcls-twincat-vacuum library, just
    like VRCNO, but it uses more of the PVs that were defined in
    ST_ValveBase.
    """
    ...


class VCN(Device):
    """
    VCN = Variable Controlled Needle valve

    This is a valve that controls the amount of flow between two gas volumes,
    rather than cutting off or opening the flow entirely.

    It corresponds to ST_VCN in the lcls-twincat-vacuum library.
    """
    position_readback = Cpt(
        EpicsSignalRO,
        ':POS_RDBK_RBV',
        kind='hinted',
        doc='valve position readback'
    )
    position_control = Cpt(
        EpicsSignalWithRBV,
        ':POS_REQ',
        kind='normal',
        doc=('requested positition to control the valve '
             '0-100%')
    )
    upper_limit = Cpt(
        EpicsSignalWithRBV,
        ':Limit',
        kind='normal',
        doc=('max upper limit position to open the valve '
             '0-100%')
    )
    interlock_ok = Cpt(
        EpicsSignalRO,
        ':ILK_OK_RBV',
        kind='normal',
        doc='interlock ok status'
    )
    open_command = Cpt(
        EpicsSignalWithRBV,
        ':OPN_SW',
        kind='normal',
        doc='Epics command to Open valve'
    )
    state = Cpt(
        EpicsSignalWithRBV,
        ':STATE',
        kind='hinted',
        doc='Valve state'
    )
    pos_ao = Cpt(
        EpicsSignalRO,
        ':POS_AO_RBV',
        kind='hinted'
    )
