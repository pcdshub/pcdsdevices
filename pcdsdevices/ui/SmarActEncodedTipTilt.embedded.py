from __future__ import annotations

import logging
from time import sleep
from typing import Optional

import ophyd
import pydm
from ophyd.status import MoveStatus
from pydm import Display
from pydm.utilities import IconFont
from qtpy import QtCore, QtGui, QtWidgets
from typhos import utils
from typhos.panel import SignalOrder, TyphosSignalPanel
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
    tip_invert_jog: QtWidgets.QCheckBox
    tip_invert_tweak: QtWidgets.QCheckBox
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
    tilt_invert_jog: QtWidgets.QCheckBox
    tilt_invert_tweak: QtWidgets.QCheckBox
    # General
    home_button: QtWidgets.QPushButton
    calibrate_button: QtWidgets.QPushButton
    sequence_progress_bar: QtWidgets.QProgressBar
    tip_expert_button: TyphosRelatedSuiteButton
    tilt_expert_button: TyphosRelatedSuiteButton


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
        def is_calibrating(device: any):
            """
            Check the 2nd bit in the channel state to see if the stage is
            currently in the calibration sequence.
            """
            _state_raw = device.channel_state_raw.get()
            # manually check the 2nd bit
            return (_state_raw & (1 << 2)) > 0

        def wait_on_calib(device):
            """
            Wait for the calibration sequence to finish.
            Needs to initially sleep for a second to let records update.
            """
            sleep(1)
            while is_calibrating(device):
                sleep(0.2)

        stage = self._motor
        sequence = [stage.tip, stage.tilt, stage.tip]
        progress = 0

        for axis in sequence:
            # Calibrate first
            self._status = axis.do_calib.put(1)
            wait_on_calib(axis)
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

        self._omit_names = ['jog_fwd', 'jog_rev']
        self.ui.extended_signal_panel = None

        self.ui.settings_button.clicked.connect(self._expand_layout)

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
            _open_loop_dict = {'jog_fwd': '_jog_fwd',
                               'jog_rev': '_jog_rev',
                               'step_count': ':TOTAL_STEP_COUNT',
                               'jog_step_size': ':STEP_COUNT'}

            for obj, _suffix in _open_loop_dict.items():
                _widget = getattr(self.ui, f'{axis}_{obj}')
                if isinstance(_widget, pydm.widgets.pushbutton.PyDMPushButton):
                    # Set the slots for the jog buttons
                    _signal = getattr(self, f'_{axis}{_suffix}')
                    _widget.clicked.connect(_signal)
                else:
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

    @QtCore.Property("QStringList")
    def omitNames(self) -> list[str]:
        """Get or set the list of names to omit in the expanded signal panel."""
        return self._omit_names

    @omitNames.setter
    def omitNames(self, omit_names: list[str]) -> None:
        if omit_names == self._omit_names:
            return

        self._omit_names = list(omit_names or [])
        if self.ui.extended_signal_panel is not None:
            self.ui.extended_signal_panel.omitNames = self._omit_names

    def get_names_to_omit(self) -> list[str]:
        """
        Get a list of signal names to omit in the extended panel.

        Returns
        -------
        list[str]
        """
        device: Optional[ophyd.Device] = self.device
        if device is None:
            return []

        to_omit = set(['jog_fwd', 'jog_rev'])

        for name in self.omitNames:
            to_omit.add(name)

        if device.name in to_omit:
            # Don't let the renamed position signal stop us from showing any
            # signals:
            to_omit.remove(device.name)
        return sorted(to_omit)

    def _create_signal_panel(self) -> Optional[TyphosSignalPanel]:
        """Create the 'extended' TyphosSignalPanel for the device."""
        if self.device is None:
            return None

        return SettingsPanel(mirror=self, parent=self, flags=QtCore.Qt.Window)

    def _expand_layout(self) -> None:
        """Toggle the expansion of the signal panel."""
        if self.ui.extended_signal_panel is None:
            self.ui.extended_signal_panel = self._create_signal_panel()
            if self.ui.extended_signal_panel is None:
                return
            to_show = True
        else:
            to_show = not self.ui.extended_signal_panel.isVisible()

        self.ui.extended_signal_panel.setVisible(to_show)

    def _jog_wrapper(self, axis: str, direction: str):
        """
        Need to abstract the jog functions from simple channel access due to strange
        pydm callback bugs when reassigning channels. Kind of defeats the point of
        using pydm buttons, but whenever that bug is fixed we can use set_channel.
        Parameters
        -----------
        axis: str
            Name of the axis, i.e. 'tip' or 'tilt'
        direction: str
            Direction of move, i.e. 'tip' or 'tilt'
        """
        invert = getattr(self.ui, f'{axis}_invert_jog').isChecked()
        stage = getattr(self.device, axis)
        _fwd = getattr(stage, 'open_loop.jog_fwd')
        _rev = getattr(stage, 'open_loop.jog_rev')

        if direction == 'Forward':
            _jog = _rev if invert else _fwd
            _jog.put(1)
        if direction == 'Reverse':
            _jog = _fwd if invert else _rev
            _jog.put(1)

    @QtCore.Slot()
    def _tip_jog_fwd(self):
        """Jog tip axis forward by tip.jog_step_size"""
        self._jog_wrapper(axis='tip', direction='Forward')

    @QtCore.Slot()
    def _tip_jog_rev(self):
        """Jog tip axis backwards by tip.jog_step_size"""
        self._jog_wrapper(axis='tip', direction='Reverse')

    @QtCore.Slot()
    def _tilt_jog_fwd(self):
        """Jog tilt axis forward by tilt.jog_step_size"""
        self._jog_wrapper(axis='tilt', direction='Forward')

    @QtCore.Slot()
    def _tilt_jog_rev(self):
        """Jog tilt axis backwards by tilt.jog_step_size"""
        self._jog_wrapper(axis='tilt', direction='Reverse')

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

    def _tweak_wrapper(self, axis: str, direction: str):
        """
        Wrapper for the tweak motor slots to minimize copypasta.

        Parameters
        -----------
        axis: str
            Name of axis, e.g. tip or tilt.
        direction: str
            Direction of the tweak button, e.g. forward or reverse.
        """
        invert = getattr(self.ui, f'{axis}_invert_tweak').isChecked()
        stage = getattr(self.device, axis)
        tweak_val = float(getattr(self.ui, f'{axis}_tweak_value').text())

        if direction == 'Reverse':
            tweak_val = - tweak_val

        tweak_val = -tweak_val if invert else tweak_val

        try:
            self.tweak_setpoint(stage, tweak_val)
        except Exception:
            logger.exception(f'{direction} tweak on {axis} failed!')

    @QtCore.Slot()
    def _tip_tweak_fwd(self):
        """Tweak positive by the amount listed in ``ui.tip_tweak_set``"""
        self._tweak_wrapper(axis='tip', direction='Forward')

    @QtCore.Slot()
    def _tip_tweak_rev(self):
        """Tweak negative by the amount listed in ``ui.tip_tweak_set``"""
        self._tweak_wrapper(axis='tip', direction='Reverse')

    @QtCore.Slot()
    def _tilt_tweak_fwd(self):
        """Tweak positive by the amount listed in ``ui.tilt_tweak_set``"""
        self._tweak_wrapper(axis='tilt', direction='Forward')

    @QtCore.Slot()
    def _tilt_tweak_rev(self):
        """Tweak negative by the amount listed in ``ui.tilt_tweak_set``"""
        self._tweak_wrapper(axis='tilt', direction='Reverse')

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


# For the record, copy-pasting this from the other tip-tilt script is ugly and makes me sad
# But all the other options are more painful, so I'll do this for now.
class _StageSettingsUI():
    """helper for the stages basic settings. Do not instantiate."""
    tip_label: QtWidgets.QLabel
    tilt_label: QtWidgets.QLabel
    step_size_label: QtWidgets.QLabel
    tip_step_size_rbv: pydm.widgets.label.PyDMLabel
    tip_step_size_set: pydm.widgets.line_edit.PyDMLineEdit
    tilt_step_size_rbv: pydm.widgets.label.PyDMLabel
    tilt_step_size_set: pydm.widgets.line_edit.PyDMLineEdit
    step_count_label: QtWidgets.QLabel
    step_count_rbv: pydm.widgets.label.PyDMLabel
    step_volt_label: QtWidgets.QLabel
    tip_step_volt_rbv: pydm.widgets.label.PyDMLabel
    tip_step_volt_set: pydm.widgets.line_edit.PyDMLineEdit
    tilt_step_volt_rbv: pydm.widgets.label.PyDMLabel
    tilt_step_volt_set: pydm.widgets.label.PyDMLineEdit


class SettingsPanel(QtWidgets.QWidget):
    """
    Container class for basic settings that accompany open-loop movement for SmarAct tip-tilts.
    Largely lifted from TyphosPositionerRow.
    """
    mirror: SmarActEncodedTipTiltWidget
    resize_timer: QtCore.QTimer

    def __init__(self, mirror: SmarActEncodedTipTiltWidget, parent: QtWidgets.QWidget | None = None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.mirror = mirror
        # Make the subdevice labels
        self.tip_label = QtWidgets.QLabel()
        self.format_label(self.tip_label, 'Tip')

        self.tilt_label = QtWidgets.QLabel()
        self.format_label(self.tilt_label, 'Tilt')

        # Then add panels, widgets, devices, and scroll areas
        self.tip_panel = TyphosSignalPanel()
        self.tip_panel.sortBy = SignalOrder.byName
        self.tip_panel.omitNames = mirror.get_names_to_omit()
        self.tip_panel.add_device(mirror.device.tip.open_loop)
        self.tip_scroll_area = QtWidgets.QScrollArea()
        self.format_scroll_area(self.tip_panel, self.tip_scroll_area)

        self.tilt_panel = TyphosSignalPanel()
        self.tilt_panel.sortBy = SignalOrder.byName
        self.tilt_panel.omitNames = mirror.get_names_to_omit()
        self.tilt_panel.add_device(mirror.device.tilt.open_loop)
        self.tilt_scroll_area = QtWidgets.QScrollArea()
        self.format_scroll_area(self.tilt_panel, self.tilt_scroll_area)

        # Then add them to the layout!
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tip_label)
        layout.addWidget(self.tip_scroll_area)
        layout.addWidget(self.tilt_label)
        layout.addWidget(self.tilt_scroll_area)

        # Set the layout and then do some resize timer set-up
        self.setLayout(layout)
        self.resize_timer = QtCore.QTimer(parent=self)
        self.resize_timer.timeout.connect(self.fix_scroll_size)
        self.resize_timer.setInterval(1)
        self.resize_timer.setSingleShot(True)

        # Capture the initial min widths
        for panel in [self.tip_panel, self.tilt_panel]:
            panel.original_panel_min_width = panel.minimumWidth()
            panel.last_resize_width = 0

        self.resize_done = False

    def format_label(self, label, label_text):
        """Create and format the text for each subdevice"""
        _label = label
        _label.setText(label_text)
        _font = _label.font()
        _font.setPointSize(_font.pointSize() + 4)
        _label.setFont(_font)
        _label.setMaximumHeight(
            QtGui.QFontMetrics(_font).boundingRect(_label.text()).height()
        )

    def format_scroll_area(self, panel, panel_scroll_area):
        """Format the scroll area for each subdevice"""
        panel_scroll_area.setFrameStyle(QtWidgets.QFrame.NoFrame)
        panel_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        panel_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        panel_scroll_area.setWidgetResizable(True)
        panel_scroll_area.setWidget(panel)

    def hideEvent(self, event: QtGui.QHideEvent):
        """
        After hide, update button text, even if we were hidden via clicking the "x".
        Shamelessly stolen from TyphosPositionerRow.
        """
        button = self.mirror.ui.settings_button
        button.PyDMIcon = 'SP_ToolBarHorizontalExtensionButton'
        return super().hideEvent(event)

    def showEvent(self, event: QtGui.QShowEvent):
        """
        Before show, update button text and move window to just under button.
        Shamelessly stolen from TyphosPositionerRow.
        """
        button = self.mirror.ui.settings_button
        button.PyDMIcon = 'SP_ToolBarVerticalExtensionButton'
        offset = button.mapToGlobal(QtCore.QPoint(0, 0))
        self.move(
            button.mapToGlobal(
                QtCore.QPoint(
                    button.pos().x() + button.width(),
                    button.pos().y() + button.height()
                    + self.style().pixelMetric(QtWidgets.QStyle.PM_TitleBarHeight)
                    - offset.y(),
                )
            )
        )
        if not self.resize_done:
            self.resize_timer.start()
        return super().showEvent(event)

    def fix_scroll_size(self):
        """
        Slot that ensures the panel gets enough space in the scroll area.

        The panel, when created, has smaller sizing information than it does
        a few moments after being shown for the first time. This might
        update several times before settling down.

        We want to watch for this resize and set the scroll area width such
        that there's enough room to see the widget at its minimum size.
        --------------------------------------------------------------------
        Also shamelessly stolen from TyphosPositionerRow
        """
        if (self.tip_panel.minimumWidth() <= self.tip_panel.original_panel_min_width or
                self.tilt_panel.minimumWidth() <= self.tilt_panel.original_panel_min_width):
            # No change
            self.resize_timer.start()
            return
        elif (self.tip_panel.last_resize_width != self.tip_panel.minimumWidth() or
                self.tilt_panel.last_resize_width != self.tilt_panel.minimumWidth()):
            # We are not stable yet!
            self.tip_panel.last_resize_width = self.tip_panel.minimumWidth()
            self.tilt_panel.last_resize_width = self.tilt_panel.minimumWidth()
            self.resize_timer.start()
            return

        def make_space(self, scroll_area, panel):
            """Generalize fixing the dimensions of the scroll areas for multiple panels"""
            scroll_area.setMinimumWidth(
                panel.minimumWidth()
                + self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)
                + 2 * self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollView_ScrollBarOverlap)
                + 2 * self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollView_ScrollBarSpacing)
            )

        make_space(self, self.tip_scroll_area, self.tip_panel)
        make_space(self, self.tilt_scroll_area, self.tilt_panel)

        self.resize_done = True
