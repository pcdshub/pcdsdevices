from __future__ import annotations

import logging
from typing import Optional

import ophyd
import pydm
from pydm import Display
from qtpy import QtCore, QtGui, QtWidgets
from typhos import utils
from typhos.panel import SignalOrder, TyphosSignalPanel

logger = logging.getLogger(__name__)


class _SmarActTipTiltEmbeddedUI(QtWidgets.QWidget):
    """Annotations helper for SmarActTipTilt.embedded.ui. Do not instantiate."""
    dpad_label: QtWidgets.QLabel
    tip_forward: pydm.widgets.pushbutton.PyDMPushButton
    tip_reverse: pydm.widgets.pushbutton.PyDMPushButton
    tip_step_count: pydm.widgets.label.PyDMLabel
    invert_tip: QtWidgets.QCheckBox
    tilt_forward: pydm.widgets.pushbutton.PyDMPushButton
    tilt_reverse: pydm.widgets.pushbutton.PyDMPushButton
    tilt_step_count: pydm.widgets.label.PyDMLabel
    invert_tilt: QtWidgets.QCheckBox
    settings_button: pydm.widgets.pushbutton.PyDMPushButton


class SmarActTipTiltWidget(Display, utils.TyphosBase):
    """Custom widget for controlling a tip-tilt with d-pad buttons"""
    ui: _SmarActTipTiltEmbeddedUI

    def __init__(self, parent=None, ui_filename='SmarActTipTilt.embedded.ui', **kwargs,):
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
            if self.ui.extended_signal_panel is not None:
                self.layout().removeWidget(self.ui.extended_signal_panel)
                self.ui.extended_signal_panel.destroyLater()
                self.ui.extended_signal_panel = None
            return

        # Can't do this during init because the device doesn't exist yet!
        self.update_pvs()

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

    def update_pvs(self):
        """
        Once we have the tip-tilt device, set the TIP and TILT channels to
        the buttons and labels.
        """
        def set_open_loop(self, axis: str):
            """
            A wrapper to set the open-loop widget channels.
            Ironically more lines than just hard coding it.
            """
            _prefix = getattr(self.device, axis).prefix
            _open_loop_dict = {'forward': '_jog_fwd',
                               'reverse': '_jog_rev',
                               'step_count': ':TOTAL_STEP_COUNT',
                               'step_size': ':STEP_COUNT'}
            for obj, _suffix in _open_loop_dict.items():
                _widget = getattr(self.ui, f'{axis}_{obj}')
                if isinstance(_widget, pydm.widgets.pushbutton.PyDMPushButton):
                    # Set the slots for the jog buttons
                    _signal = getattr(self, f'_{axis}{_suffix}')
                    _widget.clicked.connect(_signal)
                else:
                    _widget.set_channel(f'ca://{_prefix}{_suffix}')

        if self.device is None:
            print('No device set!')
            return

        set_open_loop(self, axis='tip')
        set_open_loop(self, axis='tilt')

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
        invert = getattr(self.ui, f'invert_{axis}').isChecked()
        stage = getattr(self.device, axis)
        _fwd = getattr(stage, 'jog_fwd')
        _rev = getattr(stage, 'jog_rev')

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

        # TODO: move these to a Qt designable property
        for name in self.omitNames:
            to_omit.add(name)

        if device.name in to_omit:
            # Don't let the renamed position signal stop us from showing any
            # signals:
            to_omit.remove(device.name)
        return sorted(to_omit)


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
    Container class for basic settings that accompany open-loop movement for SmarAct tip-tilts. Largely lifted from TyphosPositionerRow
    """
    mirror: SmarActTipTiltWidget
    resize_timer: QtCore.QTimer

    def __init__(self, mirror: SmarActTipTiltWidget, parent: QtWidgets.QWidget | None = None, **kwargs):
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
        self.tip_panel.add_device(mirror.device.tip)
        self.tip_scroll_area = QtWidgets.QScrollArea()
        self.format_scroll_area(self.tip_panel, self.tip_scroll_area)

        self.tilt_panel = TyphosSignalPanel()
        self.tilt_panel.sortBy = SignalOrder.byName
        self.tilt_panel.omitNames = mirror.get_names_to_omit()
        self.tilt_panel.add_device(mirror.device.tilt)
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
