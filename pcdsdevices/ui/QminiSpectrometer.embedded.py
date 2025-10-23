from __future__ import annotations

import json
import logging
import os
import re
import time

import pydm
import qtawesome as qta
from pydm import Display
from qtpy import QtWidgets
from typhos import utils

logger = logging.getLogger(__name__)


class _QminiSpectrometerEmbeddedUI(QtWidgets.QWidget):
    """Annotations helper for QminiSpectrometerEmbedded. Do not instantiate"""
    plot: pydm.widgets.PyDMWaveformPlot
    # fit parameters
    amplitude: pydm.widgets.PyDMLabel
    chisq: pydm.widgets.PyDMLabel
    fit_on: pydm.widgets.PyDMLabel
    set_fit_on: pydm.widgets.PyDMEnumComboBox
    fwhm: pydm.widgets.PyDMLabel
    st_dev: pydm.widgets.PyDMLabel
    w0_fit: pydm.widgets.PyDMLabel
    w0_guess: pydm.widgets.PyDMLabel
    w0_guess_set: pydm.widgets.PyDMLineEdit
    width: pydm.widgets.PyDMLabel
    width_set: pydm.widgets.PyDMLineEdit
    # spectrometer settings
    exposure_time: pydm.widgets.PyDMLabel
    exposure_time_set: pydm.widgets.PyDMLineEdit
    exposures_avg: pydm.widgets.PyDMLabel
    exposures_avg_set: pydm.widgets.PyDMLineEdit
    force_trigger_button: pydm.widgets.PyDMPushButton
    reinit_button: pydm.widgets.PyDMPushButton
    save_spectra_button: pydm.widgets.PyDMPushButton
    scan_rate: pydm.widgets.PyDMLabel
    scan_rate_set: pydm.widgets.PyDMEnumComboBox
    status: pydm.widgets.PyDMLabel
    temperature: pydm.widgets.PyDMLabel
    trig_enable: pydm.widgets.PyDMLabel
    trig_enable_set: pydm.widgets.PyDMEnumComboBox
    # saving spectra
    save_spectra_button: pydm.widgets.PyDMPushButton
    # graph helpers
    recolor_graph_button: QtWidgets.QPushButton


class QminiSpectrometerEmbeddedUI(Display, utils.TyphosBase):
    """
    Custom widget for managing the SmarAct detailed screen
    """
    ui: _QminiSpectrometerEmbeddedUI

    def __init__(self, parent=None, ui_filename='QminiSpectrometer.embedded.ui', **kwargs):
        super().__init__(parent=parent, ui_filename=ui_filename)

        self.ui.save_spectra_button.clicked.connect(self.save_data)
        self.ui.recolor_graph_button.clicked.connect(self.recolor_graph)
        self.ui.recolor_graph_button.setIcon(qta.icon('msc.symbol-color'))

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
            if isinstance(_widget,
                          pydm.widgets.waveformplot.PyDMWaveformPlot):
                _widget.addChannel(
                    y_channel=f'ca://{self.device.prefix}:SPECTRUM',
                    x_channel=f'ca://{self.device.prefix}:WAVELENGTHS',
                    color='black',
                    lineStyle=1,
                    lineWidth=2,
                    redraw_mode=pydm.widgets.waveformplot.WaveformCurveItem.REDRAW_ON_Y,
                    yAxisName='Intensity',
                    name='Intensity (a.u.)'
                )

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
        _button = pydm.widgets.pushbutton.PyDMPushButton
        _byte = pydm.widgets.byte.PyDMByteIndicator
        _label = pydm.widgets.label.PyDMLabel
        _line_edit = pydm.widgets.line_edit.PyDMLineEdit
        _combo_box = pydm.widgets.enum_combo_box.PyDMEnumComboBox
        _plot = pydm.widgets.waveformplot.PyDMWaveformPlot

        result = []

        for obj_type in [_button, _byte, _label, _line_edit, _combo_box, _plot]:
            result += [obj.objectName() for obj in self.findChildren(obj_type)]

        _omit = ['save_spectra']

        return [obj for obj in result if obj not in _omit]

    # Save spectra functions
    def save_data(self, **kwargs):
        """
        Save the spectrum and qmini settings to a text file.
        """
        _file = self.file_dialog()

        if not _file:
            # We got cold feet, abort!
            return

        self.device.log.info('Saving spectrum to disk...')
        # Let's format to JSON for the science folk with sinful f-string mangling
        _settings = ['sensitivity_cal', 'correct_prnu', 'correct_nonlinearity',
                     'normalize_exposure', 'adjust_offset', 'subtract_dark',
                     'remove_bad_pixels', 'remove_temp_bad_pixels']

        _data = {'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                 'exposure (us)': self.device.exposure.get(),
                 'averages': self.device.exposures_to_average.get(),
                 # Lets do some sneaky conversion to bool from int
                 'settings': {f"{sig}": bool(getattr(self.device, sig).get())
                              for sig in _settings},
                 'wavelength (nm)': [str(x) for x in self.device.wavelengths.get()],
                 'intensity (a.u.)': [str(y) for y in self.device.spectrum.get()]
                 }

        # and let's assume you have permission to save your file where you want to
        with open(_file, 'w') as _f:
            _f.write(json.dumps(_data, indent=4))

    def file_dialog(self) -> str:
        """
        Prompt the user for a save file destination.

        Returns
        ----------
        filename: str
            full path of the filename

        """
        dialog = QtWidgets.QFileDialog(self)
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
        dialog = QtWidgets.QColorDialog(self)
        color = dialog.getColor()

        if not color.isValid():
            return None

        return color.name()

    def recolor_graph(self):
        """
        Hacky recolor of an active PyDMWaveFormPlot.
        """
        _plot = self.ui.plot
        for curve in _plot._curves:
            # Have to inspect the y_channel address to figure out
            # which curve we are dealing with
            if 'SPECTRUM' in curve.y_channel.address:
                # for now, we're only plotting the main spectrum
                _old_color = curve.color
                _new_color = self.color_dialog()
                # Forgot to pick a color? Oh well, stay boring then
                if not _new_color:
                    _new_color = _old_color
                curve.color = _new_color
