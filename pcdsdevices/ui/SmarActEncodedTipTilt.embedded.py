from __future__ import annotations

import logging
from time import sleep

import pydm
from ophyd.status import MoveStatus
from pydm import Display
from pydm.utilities import IconFont
from qtpy import QtCore, QtGui, QtWidgets
from typhos import utils
from typhos.related_display import TyphosRelatedSuiteButton

logger = logging.getLogger(__name__)


class _SmarActEncodedTipTiltEmbeddedUI(QtWidgets.QWidget):
    """Annotations helper for SmarActEncodedTipTilt.embedded.ui. Do not instantiate."""
    # Open-loop
    dpad_open_loop_label: QtWidgets.QLabel
    tip_jog_fwd: pydm.widgets.pushbutton.PyDMPushButton
    tip_jog_rev: pydm.widgets.pushbutton.PyDMPushButton
    tip_step_count: pydm.widgets.label.PyDMLabel
    tilt_jog_fwd: pydm.widgets.pushbutton.PyDMPushButton
    tilt_jog_rev: pydm.widgets.pushbutton.PyDMPushButton
    tilt_step_count: pydm.widgets.label.PyDMLabel
    tip_calibrated_led: pydm.widgets.byte.PyDMByteIndicator
    tip_homed_led: pydm.widgets.byte.PyDMByteIndicator
    # Closed-loop
    dpad_closed_loop_label: QtWidgets.QLabel
    tip_tweak_fwd: pydm.widgets.pushbutton.PyDMPushButton
    tip_tweak_rev: pydm.widgets.pushbutton.PyDMPushButton
    tip_tweak_value: QtWidgets.QLineEdit
    tilt_tweak_fwd: pydm.widgets.pushbutton.PyDMPushButton
    tilt_tweak_rev: pydm.widgets.pushbutton.PyDMPushButton
    tilt_tweak_value: QtWidgets.QLineEdit
    tip_rbv: pydm.widgets.label.PyDMLabel
    tilt_rbv: pydm.widgets.label.PyDMLabel
    tilt_calibrated_led: pydm.widgets.byte.PyDMByteIndicator
    tilt_homed_led: pydm.widgets.byte.PyDMByteIndicator
    # General
    home_button: QtWidgets.QPushButton
    calibrate_button: QtWidgets.QPushButton
    sequence_progress_bar: QtWidgets.QProgressBar
    tip_expert_button: TyphosRelatedSuiteButton
    tilt_expert_button: TyphosRelatedSuiteButton
    devices: list


class MotorThread(QtCore.QThread):
    """
    Thread class for homing or calibrating a stage. Shamelessly lifted from Tyler's btms-ui work.

    Parameters
    -----------
    device: any
        The root device for the motor.

    parent: any
        The parent object to spawn the thread from

    """
    _progress = QtCore.Signal(int)
    _status: MoveStatus = None
    _finished = QtCore.Signal(bool)

    def __init__(self, device, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._motor = device
        self._success = False

    def run(self):
        """
        Overwrite this method with the code that you want to run in the thread.
        Ensure that you are checking the stopped() status and return from your
        routine when appropriate to stop execution when requested.
        """
        pass


class _home_thread(MotorThread):
    """
    Make a thread for the homing sequence and update the progress bar stored
    in the parent.
    """
    def run(self):
        stage = self._motor
        sequence = [stage.tip, stage.tilt, stage.tip]
        progress = 0

        for axis in sequence:
            self._status = axis.home('reverse', wait=True)
            self._status.wait()
            progress += 1
            self._progress.emit(int(100*(progress/len(sequence))))

        self._finished.emit(True)


class _calibrate_thread(MotorThread):
    """
    Make a thread for the calibration sequence.

    Parameters
    ----------
    device: any
        Should be either self.device.tip or self.device.tilt
    """
    def run(self):
        stage = self._motor
        sequence = [stage.tip, stage.tilt, stage.tip]
        progress = 0

        for axis in sequence:
            # Calibrate first
            self._status = axis.do_calib.put(1)
            # Have to manually sleep :[
            sleep(5)
            progress += 1
            self._progress.emit(int(100*(progress/len(2*sequence))))
            # Then home
            self._status = axis.home('reverse', wait=True)
            self._status.wait()
            progress += 1
            self._progress.emit(int(100*(progress/len(2*sequence))))

        self._finished.emit(True)


class SmarActEncodedTipTiltWidget(Display, utils.TyphosBase):
    """Custom widget for controlling a tip-tilt with d-pad buttons"""
    ui: _SmarActEncodedTipTiltEmbeddedUI

    def __init__(self, parent=None, ui_filename='SmarActEncodedTipTilt.embedded.ui', **kwargs,):
        super().__init__(parent=parent, ui_filename=ui_filename)

    @property
    def device(self):
        """The associated device."""
        try:
            return self.devices[0]
        except Exception:
            ...

    def add_device(self, device):
        """Typhos hook for adding a new device."""
        super().add_device(device)

        # Gotta make sure to destroy this screen if you were handed an empty device
        if device is None:
            self.ui.device_name_label.setText("(no device)")
            self.ui.tip_expert_button.devices.clear()
            self.ui.tilt_expert_button.devices.clear()
            return

        # Can't do this during init because the device doesn't exist yet!
        self.update_pvs()
        # Link to the expert screen buttons
        self.ui.tip_expert_button.devices.clear()
        self.ui.tip_expert_button.add_device(self.device.tip)
        self.ui.tilt_expert_button.devices.clear()
        self.ui.tilt_expert_button.add_device(self.device.tilt)

        # Have to do some UI clean-up here too for the custom home and calibrate
        # Set up the calibrate button, but only show it if either stage
        # happens to be uncalibrated, but the encoder is present. Check with a timer
        self.ui.calibrate_button.clicked.connect(self.confirm_calibrate)
        _icon = IconFont().icon('wrench', QtGui.QColor(90, 90, 90))
        self.ui.calibrate_button.setIcon(_icon)

        self.ui.sequence_progress_bar.hide()
        self.ui.sequence_progress_bar.setRange(0, 100)

        self.ui.home_button.clicked.connect(self.confirm_home)
        _icon = IconFont().icon('home', QtGui.QColor(0, 85, 255))
        self.ui.home_button.setIcon(_icon)

    def update_pvs(self):
        """
        Once we have the tip-tilt device, set the TIP and TILT channels to
        the buttons and labels.
        """

        if self.device is None:
            print('No device set!')
            return

        def set_open_loop(self, axis: str):
            """
            A wrapper to set the open-loop widget channels.
            Ironically more lines than just hard coding it.
            """
            _prefix = getattr(self.device, axis).prefix
            _open_loop_dict = {'jog_fwd': ':STEP_FORWARD.PROC',
                               'jog_rev': ':STEP_REVERSE.PROC',
                               'step_count': ':TOTAL_STEP_COUNT'}
            for obj, _suffix in _open_loop_dict.items():
                _widget = getattr(self.ui, f'{axis}_{obj}')
                _widget.set_channel(f'ca://{_prefix}{_suffix}')

        def set_closed_loop(self, axis: str):
            """
            A wrapper to set the closed-loop widget channels.
            """
            # Verbosely set the RBV widget
            _prefix = getattr(self.device, axis).prefix
            _pos_rbv = getattr(self.ui, f'{axis}_rbv')
            _pos_rbv.set_channel(f'ca://{_prefix}.RBV')

            # Then connect the tweak buttons to their slots
            for widget in ['_tweak_fwd', '_tweak_rev']:
                _widget = getattr(self.ui, f'{axis}{widget}')
                _signal = getattr(self, f'_{axis}{widget}')
                _widget.clicked.connect(_signal)

            # Then connect the byte indicators
            _led_dict = {'calibrated': ':STATE_RBV.B6',
                         'homed': ':STATE_RBV.B7'}
            for state, _suffix in _led_dict.items():
                _led = getattr(self.ui, f'{axis}_{state}_led')
                _led.set_channel(f'ca://{_prefix}{_suffix}')

        set_open_loop(self, 'tip')
        set_open_loop(self, 'tilt')
        set_closed_loop(self, 'tip')
        set_closed_loop(self, 'tilt')

    def _get_position(self, device: any):
        """
        Get the current position of the component device.
        """
        return device.user_readback.get()

    def tweak_setpoint(self, device: any, tweak_val: float):
        """
        Tweak the setpoint for a component device.
        """
        try:
            _setpoint = self._get_position(device) + tweak_val
            device.user_setpoint.put(_setpoint)
        except Exception:
            logger.exception(f'Tweak on {device} failed')

    @QtCore.Slot()
    def _tip_tweak_fwd(self):
        """Tweak positive by the amount listed in ``ui.tip_tweak_set``"""
        try:
            self.tweak_setpoint(self.device.tip,
                                float(self.ui.tip_tweak_value.text()))
        except Exception:
            logger.exception('Positive tweak failed on tip')
            return

    @QtCore.Slot()
    def _tip_tweak_rev(self):
        """Tweak negative by the amount listed in ``ui.tip_tweak_set``"""
        try:
            self.tweak_setpoint(self.device.tip,
                                -float(self.ui.tip_tweak_value.text()))
        except Exception:
            logger.exception('Negative tweak failed on tip')
            return

    @QtCore.Slot()
    def _tilt_tweak_fwd(self):
        """Tweak positive by the amount listed in ``ui.tilt_tweak_set``"""
        try:
            self.tweak_setpoint(self.device.tilt,
                                float(self.ui.tilt_tweak_value.text()))
        except Exception:
            logger.exception('Positive tweak failed on tilt')
            return

    @QtCore.Slot()
    def _tilt_tweak_rev(self):
        """Tweak negative by the amount listed in ``ui.tilt_tweak_set``"""
        try:
            self.tweak_setpoint(self.device.tilt,
                                -float(self.ui.tilt_tweak_value.text()))
        except Exception:
            logger.exception('Negative tweak failed on tilt')
            return

    @QtCore.Slot()
    def confirm_home(self):
        """
        Ask user for confirmation before homing sequence.
        """
        _result = self.confirm_move()

        if _result:
            self.home_stages()

    @QtCore.Slot()
    def confirm_calibrate(self):
        """
        Ask user for confirmation before entering calibration sequence.
        """
        _result = self.confirm_move()

        if _result:
            self.calibrate_stages()

    def confirm_move(self) -> bool:
        """
        Spawn a confirmation-dialog box similar to PyDMPushButtons.
        """
        button = self.ui.home_button
        offset = button.mapToGlobal(QtCore.QPoint(0, 0))

        _msg = QtWidgets.QMessageBox()
        _msg.setWindowTitle('Warning')
        _msg.setText('Are you sure you want to proceed?')
        _msg.setInformativeText('This will move both axes to their mechanical end-stop.')
        _msg.setIcon(QtWidgets.QMessageBox.Warning)
        _msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        # Render the box a little closer to the home button
        _msg.move(
            button.mapToGlobal(
                QtCore.QPoint(
                    button.pos().x() + button.width(),
                    button.pos().y() + button.height()
                    + self.style().pixelMetric(QtWidgets.QStyle.PM_TitleBarHeight)
                    - offset.y(),
                )
            )
        )

        result = _msg.exec_()

        if result == QtWidgets.QMessageBox.Ok:
            return True

        return False

    def update_progress(self, value: int):
        """
        Calculate the percentage of threads completed and return as int.
        """
        self.ui.sequence_progress_bar.setValue(value)

    def hide_progress(self, flag: bool):
        """
        Hide the QProgressBar when you get the flag from a signal.
        """
        if flag:
            self.ui.sequence_progress_bar.hide()

    def home_stages(self):
        """
        Home the tip-tilt stage by calling the homing thread.
        """
        self.ui.sequence_progress_bar.setValue(0)
        self.ui.sequence_progress_bar.show()
        self.ui.sequence_progress_bar.setFormat('Homing... %p%')

        self._thread = _home_thread(device=self.device)
        self._thread._progress.connect(self.update_progress)
        self._thread._finished.connect(self.hide_progress)
        self._thread.start()

    def calibrate_stages(self):
        """
        Calibration sequence is a little involved for tip-tilts.
        Vendor recommends cal A -> home A -> cal B -> home B -> cal A -> home A.
        Like home_stages, we sequence the threads to do this.
        """
        self.ui.sequence_progress_bar.setValue(0)
        self.ui.sequence_progress_bar.show()
        self.ui.sequence_progress_bar.setFormat('Calibrating... %p%')

        self._thread = _calibrate_thread(device=self.device)
        self._thread._progress.connect(self.update_progress)
        self._thread._finished.connect(self.hide_progress)
        self._thread.start()
