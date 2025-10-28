from __future__ import annotations

import logging
import re

from pydm import Display
from pydm.widgets import (PyDMByteIndicator, PyDMEnumComboBox, PyDMLabel,
                          PyDMLineEdit, PyDMPushButton)
from pydm.widgets.waveformplot import PyDMWaveformPlot, WaveformCurveItem
from qtpy.QtCore import QTimer
from typhos import utils

from pcdsdevices.widgets.qmini import QminiBase

logger = logging.getLogger(__name__)


class QminiSpectrometerEmbeddedUI(QminiBase, Display, utils.TyphosBase):
    """
    Custom widget for managing the SmarAct detailed screen

    NOTE: inherit QminiBase LAST so that self.ui exists
    """

    def __init__(self, parent=None, ui_filename='QminiSpectrometer.embedded.ui', **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename)

    def add_device(self, device):
        """Typhos hook for adding a new device."""
        super().add_device(device)
        # Gotta make sure to destroy this screen if you were handed an empty device
        if device is None:
            self.ui.device_name_label.setText("(no device)")
            return

        self.fix_pvs()

    def fix_pvs(self):
        """
        Once typhos links the device, expand the macros in the buttons and
        indicators.
        """
        if not self.device:
            print('No device set!')
            return

        def expand_prefix(channel):
            """
            containerize the macro expansion because plot objects are weird
            """
            result = ''

            if re.search(r'\{prefix\}', _channel):
                result = _channel.replace('${prefix}',
                                          self.device.prefix)
            return result

        object_names = self.find_pydm_names()

        for obj in object_names:
            _widget = getattr(self, obj)

            # setting the channels in waveform plots is weird since you cannot
            # explicitly set the x and y channels. `addChannel` adds a curve??
            if isinstance(_widget, PyDMWaveformPlot):
                _widget.addChannel(
                    y_channel=f'ca://{self.device.prefix}:SPECTRUM',
                    x_channel=f'ca://{self.device.prefix}:WAVELENGTHS',
                    color='black',
                    lineStyle=1,
                    lineWidth=2,
                    redraw_mode=WaveformCurveItem.REDRAW_ON_Y,
                    yAxisName='Spectrum',
                    name='Intensity (a.u.)'
                )

                _widget.addChannel(
                    y_channel=f'ca://{self.device.prefix}:FIT_SPECTRUM',
                    x_channel=f'ca://{self.device.prefix}:FIT_WAVELENGTHS',
                    color='red',
                    lineStyle=1,
                    lineWidth=2,
                    redraw_mode=WaveformCurveItem.REDRAW_ON_Y,
                    yAxisName='Fit',
                    name='Fit Intensity (a.u.)',
                )

                # Toggle this off since the fit spectrum causes issues
                _widget.setAutoRangeX(False)

                self._plot_timer = QTimer(parent=self)
                self._plot_timer.timeout.connect(self.fix_plot_domain)
                self._plot_timer.setInterval(200)
                self._plot_timer.start()

            # standard channel macro expansion
            else:
                _channel = getattr(_widget, 'channel')

                if not _channel:
                    _channel = ''

                _widget.set_channel(expand_prefix(_channel))

    def find_pydm_names(self) -> list[str]:
        """
        Find the object names for all PyDM objects using findChildren

        Returns
        ------------
        result : list[str]
            1D list of object names
        """
        pydm_widgets = [PyDMPushButton, PyDMByteIndicator, PyDMLabel,
                        PyDMLineEdit, PyDMEnumComboBox, PyDMWaveformPlot]

        result = []

        for obj_type in pydm_widgets:
            result += [obj.objectName() for obj in self.findChildren(obj_type)]

        _omit = ['save_spectra']

        return [obj for obj in result if obj not in _omit]

    def fix_plot_domain(self):
        """
        Pyqtgraph and PyDMWaveformPlot widgets have weird behavior when
        layering curves onto the same widget and autoranging the x-axis
        does not work as expect. Fix it when the device signals connect.
        """
        _min = int(self.device.wavelengths.get().min())
        _max = int(self.device.wavelengths.get().max())

        if not _max > _min:
            # Restart the timer if these signals are still None
            self._plot_timer.start()

        else:
            self.ui.plot.setMinXRange(_min)
            self.ui.plot.setMaxXRange(_max)
