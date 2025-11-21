from __future__ import annotations

import json
import os
import re
import time
from functools import partial

import qtawesome as qta
from ophyd import Device
from pydm.widgets import (PyDMByteIndicator, PyDMEnumComboBox, PyDMLabel,
                          PyDMLineEdit, PyDMPushButton)
from pydm.widgets.waveformplot import PyDMWaveformPlot, WaveformCurveItem
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QColorDialog, QFileDialog, QPushButton, QWidget


class _QminiBaseUI(QWidget):
    """Annotations helper for QminiSpectrometerEmbedded. Do not instantiate"""
    plot: PyDMWaveformPlot
    hide_fit_button: QPushButton
    recolor_graph_button: QPushButton
    recolor_fit_button: QPushButton
    save_spectra_button: PyDMPushButton
    toggle_fit_button: QPushButton


class QminiBase:
    """
    Base functionality for QMiniSpectrometer uis
    """
    ui: _QminiBaseUI
    devices: list[Device]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.ui.save_spectra_button.clicked.connect(self.save_data)
        for plot in ['graph', 'fit']:
            _button = getattr(self.ui, f'recolor_{plot}_button')
            _button.setIcon(qta.icon('msc.symbol-color'))
            if plot == 'graph':
                _button.clicked.connect(partial(self.recolor_graph, 'Spectrum'))
            else:
                _button.clicked.connect(partial(self.recolor_graph, 'Fit'))

        # Some properties to help us mess with the fitted curve later
        self._fit_color = 'red'
        self.ui.toggle_fit_button.clicked.connect(self.toggle_fit)
        self._fit_toggle = 1

    def add_device(self, device):
        """Typhos hook for adding a new device."""
        super().add_device(device)
        # Gotta make sure to destroy this screen if you were handed an empty device
        if device is None:
            self.ui.device_name_label.setText("(no device)")
            return

        self.fix_pvs()

        # subscribe the callback only after the PVs have been expanded
        self._autorange_cid = self.device.spectrum.subscribe(self.auto_range_y)

    @property
    def device(self):
        """The associated device."""
        try:
            return self.devices[0]
        except Exception:
            ...

    def fix_pvs(self):
        """
        Once typhos links the device, expand the macros in the buttons and
        indicators.
        """
        if not self.device:
            print('No device set!')
            return

        def expand_prefix(chan_address: str) -> str:
            """
            Factory function for macro expansion on `${prefix}`
            """
            result = ''

            if re.search(r'\{prefix\}', chan_address):
                result = chan_address.replace('${prefix}',
                                              self.device.prefix)
            return result

        object_names = self.find_pydm_names()

        for obj in object_names:
            widget = getattr(self, obj)

            # setting the channels in waveform plots is weird since you cannot
            # explicitly set the x and y channels. `addChannel` adds a curve??
            if isinstance(widget, PyDMWaveformPlot):
                widget.addChannel(
                    y_channel=f'ca://{self.device.prefix}:SPECTRUM',
                    x_channel=f'ca://{self.device.prefix}:WAVELENGTHS',
                    color='black',
                    lineStyle=1,
                    lineWidth=2,
                    redraw_mode=WaveformCurveItem.REDRAW_ON_Y,
                    yAxisName='Spectrum',
                    name='Intensity (a.u.)'
                )

                widget.addChannel(
                    y_channel=f'ca://{self.device.prefix}:FIT_SPECTRUM',
                    x_channel=f'ca://{self.device.prefix}:FIT_WAVELENGTHS',
                    color=self._fit_color,
                    lineStyle=1,
                    lineWidth=2,
                    redraw_mode=WaveformCurveItem.REDRAW_ON_Y,
                    yAxisName='Fit',
                    name='Fit Intensity (a.u.)',
                )

                # Toggle this off since the fit spectrum causes issues
                widget.setAutoRangeX(False)
                widget.setAutoRangeY(False)

                self._plot_timer = QTimer(parent=self)
                self._plot_timer.timeout.connect(self.fix_plot_domain)
                self._plot_timer.setInterval(200)
                self._plot_timer.start()

            # standard channel macro expansion
            else:
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
        plot = self.ui.plot
        x_min = int(self.device.wavelengths.get().min())
        x_max = int(self.device.wavelengths.get().max())

        if not x_max > x_min:
            # Restart the timer if these signals are still None
            self._plot_timer.start()

        else:
            plot.setMinXRange(x_min)
            plot.setMaxXRange(x_max)

    def auto_range_y(self, value, *args, **kwargs):
        """
        Callback function for updating autorange on the y-axis
        """
        plot = self.ui.plot

        y_min = int(value.min())
        y_max = int(value.max())

        if not y_max > y_min:
            return

        else:
            try:
                plot.setMinYRange(y_min)
                plot.setMaxYRange(1.1*y_max)
            except RuntimeError:
                # We must've deleted the plot without unsubscribing, do it!
                self.device.spectrum.unsubscribe(self._autorange_cid)

    # Save spectra functions
    def save_data(self, **kwargs):
        """
        Save the spectrum and qmini settings to a text file.
        """

        file = self.file_dialog()

        if not file:
            # We got cold feet, abort!
            return

        self.device.log.info('Saving spectrum to disk...')
        # Let's format to JSON for the science folk with sinful f-string mangling
        settings = ['sensitivity_cal', 'correct_prnu', 'correct_nonlinearity',
                    'normalize_exposure', 'adjust_offset', 'subtract_dark',
                    'remove_bad_pixels', 'remove_temp_bad_pixels']

        data = {'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'exposure (us)': self.device.exposure.get(),
                'averages': self.device.exposures_to_average.get(),
                # Lets do some sneaky conversion to bool from int
                'settings': {f"{sig}": bool(getattr(self.device, sig).get())
                             for sig in settings},
                'wavelength (nm)': [str(x) for x in self.device.wavelengths.get()],
                'intensity (a.u.)': [str(y) for y in self.device.spectrum.get()]
                }

        # and let's assume you have permission to save your file where you want to
        with open(file, 'w') as _f:
            _f.write(json.dumps(data, indent=4))

    def file_dialog(self) -> str:
        """
        Prompt the user for a save file destination.

        Returns
        ----------
        filename: str
            full path of the filename

        """
        dialog = QFileDialog(self)
        filename = dialog.getSaveFileName(caption='Select name for file',
                                          dir=os.getcwd(),
                                          filter='Text files (*.txt, *.csv)',
                                          )
        # We don't care about the filter info, just give us the filename bro
        return filename[0]

    def color_dialog(self) -> str:
        """
        Prompt the user for a color.

        Returns
        ---------
        color: str
            Hex code for color represented as a string.
        """
        dialog = QColorDialog(self)
        color = dialog.getColor()

        if not color.isValid():
            return None

        return color.name()

    def recolor_graph(self, yAxisName: str):
        """
        Hacky recolor of an active PyDMWaveFormPlot.
        """
        plot = self.ui.plot

        for curve in plot._curves:
            # Have to inspect the y_channel address to figure out
            # which curve we are dealing with
            if curve.y_axis_name == yAxisName:
                # for now, we're only plotting the main spectrum
                _old_color = curve.color
                _new_color = self.color_dialog()
                # Forgot to pick a color? Oh well, stay boring then
                if not _new_color:
                    _new_color = _old_color

                self._fit_color = curve.color = _new_color
                plot.getPlotItem().setLabel(yAxisName,
                                            text='Intensity',
                                            units='a.u.',
                                            color=_new_color)

    def toggle_fit(self):
        """
        Toggle the display of the fitted curve to the plot.
        """
        plot = self.ui.plot

        if self._fit_toggle > 0:
            self.ui.toggle_fit_button.setText('show')
            temp = 0
        else:
            self.ui.toggle_fit_button.setText('hide')
            temp = 1

        for curve in plot._curves:
            if curve.y_axis_name == 'Fit':
                curve.lineStyle = temp
                curve.lineWidth = 2*temp

        self._fit_toggle = temp
