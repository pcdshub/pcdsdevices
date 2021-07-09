"""
Standard classes for LCLS Gate Valves.
"""
import logging
from enum import IntEnum

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
    open_limit = Cpt(EpicsSignalRO, ':OPN_DI', kind='normal')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI', kind='normal')

    # Commands and Interlock information
    command = Cpt(EpicsSignal, ':OPN_SW', kind='omitted')
    commands = Commands
    interlock = Cpt(EpicsSignalRO, ':OPN_OK', kind='normal')

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
    """

    open_command = Cpt(EpicsSignalWithRBV, ':OPN_SW', kind='normal',
                       doc='Epics command to Open valve')
    interlock_ok = Cpt(EpicsSignalRO, ':OPN_OK_RBV', kind='normal',
                       doc='Valve is OK to Open interlock ')
    open_do = Cpt(EpicsSignalRO, ':OPN_DO_RBV', kind='normal',
                  doc='PLC Output to Open valve, 1 means 24V on command cable')
    error_reset = Cpt(EpicsSignalWithRBV, ':ALM_RST', kind='normal',
                      doc='Reset Error state to valid by toggling this')


class VVC(ValveBase):
    """Vent Valve, Controlled."""
    override_status = Cpt(EpicsSignalRO, ':OVRD_ON_RBV', kind='omitted',
                          doc='Epics Readback on Override mode')
    override_force_open = Cpt(EpicsSignalWithRBV, ':FORCE_OPN', kind='omitted',
                              doc=('Epics Command to force open the valve in'
                                   'override mode'))


class VGCLegacy(ValveBase):
    """
    Class for Basic Vacuum Valve.

    Replaces the `GateValve` class.
    """

    open_limit = Cpt(EpicsSignalRO, ':OPN_DI_RBV', kind='hinted',
                     doc='Open limit switch digital input')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI_RBV', kind='hinted',
                       doc='Closed limit switch digital input')


class VRC(VVC, LightpathMixin):
    """Class for Gate Valves with Control and readback."""

    # Configuration for lightpath
    lightpath_cpts = ['open_limit', 'closed_limit']
    _icon = 'fa.hourglass'

    state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='normal', doc='Valve state')
    open_limit = Cpt(EpicsSignalRO, ':OPN_DI_RBV', kind='hinted',
                     doc='Open limit switch digital input')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI_RBV', kind='hinted',
                       doc='Closed limit switch digital input')

    def _set_lightpath_states(self, lightpath_values):
        """Callback for updating inserted/removed for lightpath."""

        self._inserted = lightpath_values[self.closed_limit]['value']
        self._removed = lightpath_values[self.open_limit]['value']


class VGC(VRC):
    """Class for Controlled Gate Valves."""
    diff_press_ok = Cpt(EpicsSignalRO, ':DP_OK_RBV', kind='normal',
                        doc='Differential pressure interlock ok')
    ext_ilk_ok = Cpt(EpicsSignalRO, ':EXT_ILK_OK_RBV', kind='normal',
                     doc='External interlock ok')
    at_vac_setpoint = Cpt(EpicsSignalWithRBV, ':AT_VAC_SP', kind='config',
                          doc='AT VAC Set point value')
    setpoint_hysterisis = Cpt(EpicsSignalWithRBV, ':AT_VAC_HYS', kind='config',
                              doc='AT VAC Hysterisis')
    at_vac = Cpt(EpicsSignalRO, ':AT_VAC_RBV', kind='normal',
                 doc='at vacuum sp is reached')
    error = Cpt(EpicsSignalRO, ':ERROR_RBV', kind='normal',
                doc='Error Present')
    mps_state = Cpt(EpicsSignalRO, ':MPS_FAULT_OK_RBV', kind='omitted',
                    doc=('individual valve MPS state for debugging'))
    interlock_device_upstream = Cpt(EpicsSignalRO, ':ILK_DEVICE_US_RBV',
                                    kind='config', string=True,
                                    doc='Upstream vacuum device used for'
                                    'interlocking this valve')
    interlock_device_downstream = Cpt(EpicsSignalRO, ':ILK_DEVICE_DS_RBV',
                                      kind='config', string=True,
                                      doc='Downstream vacuum device used for'
                                      'interlocking this valve')


class VGC_2S(VGC):
    """Class for Controlled Gate Valves with 2 setpoints."""
    at_vac_setpoint_ds = Cpt(EpicsSignalWithRBV, ':AT_VAC_SP_DS',
                             kind='config',
                             doc='AT VAC Set point value '
                                 'for the downstream gauge')
    setpoint_hysterisis_ds = Cpt(EpicsSignalWithRBV, ':AT_VAC_HYS_DS',
                                 kind='config',
                                 doc='AT VAC Hysterisis for '
                                     'the downstream setpoint')


class VFS(Device, LightpathMixin):
    """Class for Fast Shutter Valve."""

    # Configuration for lightpath
    lightpath_cpts = ['position_open', 'position_close']
    _icon = 'fa.shield'

    valve_position = Cpt(EpicsSignalRO, ':POS_STATE_RBV', kind='hinted',
                         doc='Ex: OPEN, CLOSED, MOVING, INVALID, OPEN_F')
    vfs_state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='hinted',
                    doc='Fast Shutter Current State')
    request_close = Cpt(EpicsSignalWithRBV, ':CLS_SW', kind='normal',
                        doc=('Request Fast Shutter to Close. When both close'
                             'and open are requested, VFS will close.'))
    request_open = Cpt(EpicsSignalWithRBV, ':OPN_SW', kind='normal',
                       doc=('Request Fast Shutter to Open. Requires a rising'
                            'EPICS signal to open. When both close and'
                            'open are requested, VFS will close.'))
    reset_vacuum_fault = Cpt(EpicsSignalWithRBV, ':ALM_RST', kind='normal',
                             doc=('Reset Fast Shutter Vacuum Faults: fast'
                                  'sensor triggered, fast sensor turned off.'
                                  'To open VFS, this needs to be reset to TRUE'
                                  'after a vacuum event.'))
    override_mode = Cpt(EpicsSignalWithRBV, ':OVRD_ON', kind='normal',
                        doc='Epics Command to set Override mode')
    override_force_open = Cpt(EpicsSignalWithRBV, ':FORCE_OPN',
                              kind='normal',
                              doc=('Epics Command to force open'
                                   'the valve in override mode'))
    gfs_name = Cpt(EpicsSignalRO, ':GFS_RBV', kind='normal', string=True,
                   doc='Gauge Fast Sensor Name')
    gfs_trigger = Cpt(EpicsSignalRO, ':TRIG_RBV', kind='normal',
                      doc='Gauge Fast Sensor Input Trigger')
    position_close = Cpt(EpicsSignalRO, ':CLS_DI_RBV', kind='normal',
                         doc='Fast Shutter Closed Valve Position')
    position_open = Cpt(EpicsSignalRO, ':OPN_DI_RBV', kind='normal',
                        doc='Fast Shutter Open Valve Position')
    vac_fault_ok = Cpt(EpicsSignalRO, ':VAC_FAULT_OK_RBV', kind='normal',
                       doc=('Fast Shutter Vacuum Fault OK Readback'))
    mps_ok = Cpt(EpicsSignalRO, ':MPS_FAULT_OK_RBV', kind='normal',
                 doc='Fast Shutter Fast Fault Output OK')
    veto_device = Cpt(EpicsSignalRO, ':VETO_DEVICE_RBV',
                      kind='normal', string=True,
                      doc='Name of device that can veto this VFS')

    def _set_lightpath_states(self, lightpath_values):
        self._inserted = lightpath_values[self.position_close]['value']
        self._removed = lightpath_values[self.position_open]['value']


class VVCNO(Device):
    """Vent Valve, Controlled, Normally Open."""
    close_command = Cpt(EpicsSignalWithRBV, ':CLS_SW', kind='normal',
                        doc='Epics command to close valve')
    close_override = Cpt(EpicsSignalWithRBV, ':FORCE_CLS', kind='omitted',
                         doc=('Epics Command for open the valve in override '
                              'mode'))
    override_on = Cpt(EpicsSignalWithRBV, ':OVRD_ON', kind='omitted',
                      doc='Epics Command to set/reset Override mode')
    close_ok = Cpt(EpicsSignalRO, ':CLS_OK_RBV', kind='normal',
                   doc='used for normally open valves')
    close_do = Cpt(EpicsSignalRO, ':CLS_DO_RBV', kind='normal',
                   doc='PLC Output to close valve')


class VRCNO(VVCNO, LightpathMixin):
    """Gate Valve, Controlled, Normally Open."""

    # Configuration for lightpath
    lightpath_cpts = ['open_limit', 'closed_limit']
    _icon = 'fa.hourglass'

    state = Cpt(EpicsSignalRO, ':STATE_RBV', kind='normal', doc='Valve state')

    error_reset = Cpt(EpicsSignalWithRBV, ':ALM_RST', kind='normal',
                      doc='Reset Error state to valid by toggling this')
    open_limit = Cpt(EpicsSignalRO, ':OPN_DI_RBV', kind='hinted',
                     doc='Open limit switch digital input')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI_RBV', kind='hinted',
                       doc='Closed limit switch digital input')

    def _set_lightpath_states(self, lightpath_values):
        """Callback for updating inserted/removed for lightpath."""

        self._inserted = lightpath_values[self.closed_limit]['value']
        self._removed = lightpath_values[self.open_limit]['value']


class VCN(Device):
    """Class for Variable Controlled Needle Valves."""
    position_readback = Cpt(EpicsSignalRO, ':POS_RDBK_RBV', kind='hinted',
                            doc='valve position readback')
    position_control = Cpt(EpicsSignalWithRBV, ':POS_REQ', kind='normal',
                           doc=('requested positition to control the valve '
                                '0-100%'))
    upper_limit = Cpt(EpicsSignalWithRBV, ':Limit', kind='normal',
                      doc=('max upper limit position to open the valve '
                           '0-100%'))
    interlock_ok = Cpt(EpicsSignalRO, ':ILK_OK_RBV', kind='normal',
                       doc='interlock ok status')
    open_command = Cpt(EpicsSignalWithRBV, ':OPN_SW', kind='normal',
                       doc='Epics command to Open valve')
    state = Cpt(EpicsSignalWithRBV, ':STATE', kind='hinted', doc='Valve state')
    pos_ao = Cpt(EpicsSignalRO, ':POS_AO_RBV', kind='hinted')
