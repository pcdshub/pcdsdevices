from __future__ import annotations

import json
import os
import time

import qtawesome as qta
from ophyd import Device
from pydm.widgets import PyDMPushButton
from pydm.widgets.waveformplot import PyDMWaveformPlot
from qtpy.QtWidgets import QColorDialog, QFileDialog, QPushButton, QWidget


class _QminiBaseUI(QWidget):
    """Annotations helper for QminiSpectrometerEmbedded. Do not instantiate"""
    plot: PyDMWaveformPlot
    save_spectra_button: PyDMPushButton
    recolor_graph_button: QPushButton


class QminiBase:
    """
    Base functionality for QMiniSpectrometer uis
    """
    ui: _QminiBaseUI = _QminiBaseUI
    devices: list[Device]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

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

    def recolor_graph(self):
        """
        Hacky recolor of an active PyDMWaveFormPlot.
        """
        _plot = self.ui.plot
        for curve in _plot._curves:
            # Have to inspect the y_channel address to figure out
            # which curve we are dealing with
            if curve.y_axis_name == 'Spectrum':
                # for now, we're only plotting the main spectrum
                _old_color = curve.color
                _new_color = self.color_dialog()
                # Forgot to pick a color? Oh well, stay boring then
                if not _new_color:
                    _new_color = _old_color
                curve.color = _new_color
