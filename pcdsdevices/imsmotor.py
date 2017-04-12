from ophyd import EpicsMotor
from ophyd.device import Component
from ophyd.signal import Signal

class IMSMotor(EpicsMotor):
    """
    Subclass of EpicsMotor to deal with our IOC that's missing the .TDIR field.
    The correct solution is to fix our IMS record, this is a temporary
    band-aid.
    """
    # Disable missing field that our IMS module lacks
    direction_of_travel = Component(Signal)

    # Unfortunately I have to copy this and change the few lines that rely
    # on direction of travel (.TDIR). This may give us bad outputs if we
    # move away from a limit switch but are still tripping it.
    def _move_changed(self, timestamp=None, value=None, sub_type=None,
                      **kwargs):
        '''Callback from EPICS, indicating that movement status has changed'''
        was_moving = self._moving
        self._moving = (value != 1)

        started = False
        if not self._started_moving:
            started = self._started_moving = (not was_moving and self._moving)

        logger.debug('[ts=%s] %s moving: %s (value=%s)', fmt_time(timestamp),
                     self, self._moving, value)

        if started:
            self._run_subs(sub_type=self.SUB_START, timestamp=timestamp,
                           value=value, **kwargs)

        if was_moving and not self._moving:
            success = True
            if self.low_limit_switch.get() == 1:
                success = False
            if self.high_limit_switch.get() == 1:
                success = False

            severity = self.user_readback.alarm_severity

            if severity != AlarmSeverity.NO_ALARM:
                status = self.user_readback.alarm_status
                logger.error('Motion failed: %s is in an alarm state '
                             'status=%s severity=%s',
                             self.name, status, severity)
                success = False

            self._done_moving(success=success, timestamp=timestamp, value=value)
