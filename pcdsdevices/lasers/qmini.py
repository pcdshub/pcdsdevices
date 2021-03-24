import logging

from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as Cpt,
                   FormattedComponent as FCpt)

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
    scan_rate = Cpt(EpicsSignal, ':GET_SPECTRUM.SCAN', kind='config')
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
