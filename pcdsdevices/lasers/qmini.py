import json
import logging
import os
import time

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt
from ophyd.signal import AttributeSignal, Signal

from pcdsdevices.variety import set_metadata

logger = logging.getLogger(__name__)


class QminiSpectrometer(Device):
    """
    Qmini Spectrometer

    Device for the Qmini spectrometer by RGB Photonics.

    Parameters
    ----------
    prefix : str
        Base prefix of the Qmini

    name : str
        Name of Qmini object
    """

    # General control
    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')
    temperature = Cpt(EpicsSignalRO, ':TEMP', kind='config')
    exposure = Cpt(EpicsSignal, ':GET_EXPOSURE_TIME',
                   write_pv=':SET_EXPOSURE_TIME', kind='config')
    trig_mode = Cpt(EpicsSignal, ':TRIG_MODE_RBV', write_pv=':TRIG_MODE',
                    kind='config')
    trig_delay = Cpt(EpicsSignal, ':GET_TRIG_DELAY',
                     write_pv=':SET_TRIG_DELAY', kind='config')
    trig_pin = Cpt(EpicsSignal, ':TRIG_PIN_RBV', write_pv=':SET_TRIG_PIN',
                   kind='config')
    trig_edge = Cpt(EpicsSignal, ':TRIG_EDGE_RBV', write_pv=':SET_TRIG_EDGE',
                    kind='config')
    trig_enable = Cpt(EpicsSignal, ':GET_TRIG_ENABLE',
                      write_pv=':SET_TRIG_ENABLE', kind='config')
    acquisition_mode = Cpt(EpicsSignal, ':SOFT_TRIGGER_MODE', kind='config')
    exposures_to_average = Cpt(EpicsSignal, ':SET_AVG_CNT', kind='config')
    force_trig = Cpt(EpicsSignal, ':START_EXPOSURE.PROC', kind='config')
    set_metadata(force_trig, dict(variety='command-proc', value=1))
    reset = Cpt(EpicsSignal, ':CLEAR_SPECTROMETER', kind='config')
    set_metadata(reset, dict(variety='command-proc', value=1))
    spectrum = Cpt(EpicsSignalRO, ':SPECTRUM', kind='normal')
    wavelengths = Cpt(EpicsSignalRO, ':WAVELENGTHS', kind='normal')

    model = Cpt(EpicsSignalRO, ':MODEL_CODE', kind='config')
    set_metadata(model, dict(variety='scalar', display_format='hex'))
    serial_number = Cpt(EpicsSignalRO, ':SERIAL_NUMBER', kind='config')

    # Processing Steps
    adjust_offset = Cpt(EpicsSignal, ':ADJUST_OFFSET', kind='omitted')
    correct_nonlinearity = Cpt(EpicsSignal, ':CORRECT_NONLINEARITY',
                               kind='omitted')
    remove_bad_pixels = Cpt(EpicsSignal, ':REMOVE_BAD_PIXELS',
                            kind='omitted')
    subtract_dark = Cpt(EpicsSignal, ':SUBTRACT_DARK', kind='omitted')
    remove_temp_bad_pixels = Cpt(EpicsSignal, ':REMOVE_TEMP_BAD_PIXELS',
                                 kind='omitted')
    normalize_exposure = Cpt(EpicsSignal, ':NORMALIZE_EXPOSURE',
                             kind='omitted')
    sensitivity_cal = Cpt(EpicsSignal, ':SENSITIVITY_CAL', kind='omitted')
    correct_prnu = Cpt(EpicsSignal, ':CORRECT_PRNU', kind='omitted')
    additional_filtering = Cpt(EpicsSignal, ':ADDITIONAL_FILTERING',
                               kind='omitted')
    scale_to_16_bit = Cpt(EpicsSignal, ':SCALE_TO_16BIT', kind='omitted')
    set_processing_steps = Cpt(EpicsSignal, ':SET_PROCESSING_STEPS',
                               kind='omitted')
    get_processing_steps = Cpt(EpicsSignalRO, ':GET_PROCESSING_STEPS',
                               kind='omitted')

    # Spectral fitting
    fit_on = Cpt(EpicsSignal, ':FIT_ON', kind='config')
    fit_width = Cpt(EpicsSignal, ':WIDTH', kind='config')
    w0_guess = Cpt(EpicsSignal, ':W0_GUESS', kind='config')
    w0_fit = Cpt(EpicsSignalRO, ':W0_FIT', kind='normal')
    fit_fwhm = Cpt(EpicsSignalRO, ':FWHM', kind='config')
    fit_amplitude = Cpt(EpicsSignalRO, ':AMPLITUDE', kind='config')
    fit_stdev = Cpt(EpicsSignalRO, ':STDEV', kind='config')
    fit_chisq = Cpt(EpicsSignalRO, ':CHISQ', kind='config')

    # Save spectra functions
    def save_data(self, file_dest: str = ''):
        """
        Save the wavelength and spectrum PVs to a text file
        """
        # Let's check to see if we set this in a non-gui context
        if not file_dest.strip():
            # let's try to use the signal instead
            if not self.file_dest.get().strip():
                # set a default destination for the file we didn't set it
                _file = (os.getcwd() + '/' + self.name
                         + time.strftime("_%Y-%m-%d_%H%M%S") + '.txt')
            # otherwise just use it, silly
            else:
                _file = self.file_dest.get()
        else:
            _file = file_dest
        self.log.info('Saving spectrum to disk...')
        # Let's format to JSON for the science folk with sinful f-string mangling
        _settings = ['sensitivity_cal', 'correct_prnu', 'correct_nonlinearity',
                     'normalize_exposure', 'adjust_offset', 'subtract_dark',
                     'remove_bad_pixels', 'remove_temp_bad_pixels']
        _data = {'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                 'exposure (us)': self.exposure.get(),
                 'averages': self.exposures_to_average.get(),
                 # Lets do some sneaky conversion to bool from int
                 'settings': {f"{sig}": bool(getattr(self, sig).get())
                              for sig in _settings},
                 'wavelength (nm)': [str(x) for x in self.wavelengths.get()],
                 'intensity (a.u.)': [str(y) for y in self.spectrum.get()]
                 }
        # and let's assume you have permission to save your file where you want to
        with open(_file, 'w') as _f:
            _f.write(json.dumps(_data))

    save_spectrum = Cpt(AttributeSignal, attr='_save_spectrum', kind='omitted')
    file_dest = Cpt(Signal, value='', kind='omitted')
    set_metadata(save_spectrum, dict(variety='command-proc', value=1))

    @property
    def _save_spectrum(self):
        return 0

    # Setter will just save the data
    @_save_spectrum.setter
    def _save_spectrum(self, value):
        self.save_data()


class QminiWithEvr(QminiSpectrometer):
    """
    A class for Qmini spectrometers that use an EVR for hardware triggering.
    """
    def __init__(self, prefix, *args, evr_pv=None, evr_ch=None, **kwargs):
        self._evr_pv = evr_pv
        self._evr_ch = evr_ch

        super().__init__(prefix, **kwargs)

    event_code = FCpt(EpicsSignal, '{self._evr_pv}:TRIG{self._evr_ch}:EC_RBV',
                      write_pv='{self._evr_pv}:TRIG{self._evr_ch}:TEC',
                      kind='config')
    evr_width = FCpt(EpicsSignal,
                     '{self._evr_pv}:TRIG{self._evr_ch}:BW_TWIDCALC',
                     write_pv='{self._evr_pv}:TRIG{self._evr_ch}:TWID',
                     kind='config')
    evr_delay = FCpt(EpicsSignal, '{self._evr_pv}:TRIG{self._evr_ch}:BW_TDES',
                     write_pv='{self._evr_pv}:TRIG{self._evr_ch}:TDES',
                     kind='config')
