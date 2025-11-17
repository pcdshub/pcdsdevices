from __future__ import annotations

import logging
import pathlib
import re
from typing import Optional

from pydm import Display
from pydm.widgets import (PyDMByteIndicator, PyDMEnumComboBox, PyDMLabel,
                          PyDMLineEdit, PyDMPushButton)
from qtpy import uic
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QPushButton, QWidget
from typhos import utils

from pcdsdevices.widgets.qmini import QminiBase, _QminiBaseUI

logger = logging.getLogger(__name__)


class _QminiSpectrometerEmbeddedUI(_QminiBaseUI):
    fit_settings_button: QPushButton
    qmini_settings_button: QPushButton
    settings_panel: Optional[QWidget]
    settings_panel_resize_timer: QTimer
    parameters_panel: Optional[QWidget]
    parameters_panel_resize_timer: QTimer


class QminiSpectrometerEmbeddedUI(QminiBase, Display, utils.TyphosBase):
    """
    Custom widget for managing the SmarAct detailed screen

    NOTE: inherit QminiBase FIRST so that the mro resolves it LAST
    """
    ui: _QminiSpectrometerEmbeddedUI

    def __init__(self, parent=None, ui_filename='QminiSpectrometer.embedded.ui', **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename)

        self.ui.fit_settings_button.clicked.connect(self._open_fit_settings_panel)
        self.ui.qmini_settings_button.clicked.connect(self._open_fit_params_panel)

    def _open_fit_settings_panel(self) -> None:
        """Toggle the expansion of the signal panel."""
        if not hasattr(self.ui, 'settings_panel'):
            self.ui.settings_panel = self._create_signal_panel('fit')
            if self.ui.settings_panel is None:
                return
            to_show = True
        else:
            to_show = not self.ui.settings_panel.isVisible()

        self.ui.settings_panel.setVisible(to_show)

    def _open_fit_params_panel(self) -> None:
        """Toggle the expansion of the signal panel."""
        if not hasattr(self.ui, 'parameters_panel'):
            self.ui.parameters_panel = self._create_signal_panel('parameters')
            if self.ui.parameters_panel is None:
                return
            to_show = True
        else:
            to_show = not self.ui.parameters_panel.isVisible()

        self.ui.parameters_panel.setVisible(to_show)

    def _create_signal_panel(self, panel: str):
        """Create the signal panel for the device."""
        if (self.device is None) or (not panel):
            return

        subwindow_dir = pathlib.Path(__file__).parent / "qmini_subwindows"

        if panel == 'fit':
            ui_filename = pathlib.Path(subwindow_dir) / 'qmini_fit_settings.ui'
            return SettingsPanel(spectrometer=self,
                                 ui_filename=ui_filename,
                                 toggle_button=self.ui.fit_settings_button,
                                 parent=self, flags=Qt.Window)

        elif panel == 'parameters':
            ui_filename = pathlib.Path(subwindow_dir) / 'qmini_parameters.ui'
            return SettingsPanel(spectrometer=self,
                                 ui_filename=ui_filename,
                                 toggle_button=self.ui.qmini_settings_button,
                                 parent=self, flags=Qt.Window)
        else:
            return


class SettingsPanel(QWidget):
    """
    Container class for spawning and organizing signals in a floating window.
    """
    spectrometer: QminiSpectrometerEmbeddedUI
    panel: QWidget
    resize_timer: QTimer

    def __init__(self, spectrometer: QminiSpectrometerEmbeddedUI,
                 ui_filename: str,
                 toggle_button: QPushButton,
                 parent: QWidget | None = None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        uic.loadUi(ui_filename, self)
        self.spectrometer = spectrometer
        self.toggle_button = toggle_button

        self.fix_pvs()

        self.adjustSize()

    def fix_pvs(self):
        """
        Once typhos links the device, expand the macros in the buttons and
        indicators.
        """
        if not self.spectrometer.device:
            print('No device set!')
            return

        def expand_prefix(chan_address: str) -> str:
            """
            Factory function for macro expansion on `${prefix}`
            """
            result = ''

            prefix = self.spectrometer.device.prefix

            if re.search(r'\{prefix\}', chan_address):
                result = chan_address.replace('${prefix}',
                                              prefix)
            return result

        object_names = self.find_pydm_names()

        for obj in object_names:
            widget = getattr(self, obj)

            channel = getattr(widget, 'channel')

            if not channel:
                channel = ''

            widget.set_channel(expand_prefix(channel))

    def find_pydm_names(self) -> list[str]:
        """
        Find the object names for all PyDM objects using findChildren

        Returns
        ------------
        result : list[str]
            1D list of object names
        """
        pydm_widgets = [PyDMPushButton, PyDMByteIndicator, PyDMLabel,
                        PyDMLineEdit, PyDMEnumComboBox]

        result = []

        for obj_type in pydm_widgets:
            result += [obj.objectName() for obj in self.findChildren(obj_type)]

        _omit = ['save_spectra']

        return [obj for obj in result if obj not in _omit]
