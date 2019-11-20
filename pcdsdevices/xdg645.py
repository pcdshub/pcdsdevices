"""
Module for DG645 delay generator timing channel.
"""
from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.utils import LimitError


class DelayChannel(Device):
    """
    Class that defines an output (delay) channel of a DG645 delay generator.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, i.e 'MEC:LAS:DDG:01:a'

    name : ``str``
        Alias for the delay generator

    delay_limits : ``tuple``, optional
        Limits on the allowed delay in seconds. By default, the
        limits are set to (0.0, 1.0).
    """
    delay = Cpt(EpicsSignal, 'DelayAO', write_pv='DelaySI', kind='hinted')
    delay_tweak = Cpt(EpicsSignal, 'DelayTweakAO', kind='config')
    delay_inc = Cpt(EpicsSignal, 'DelayTweakIncCO.PROC', kind='normal')
    delay_dec = Cpt(EpicsSignal, 'DelayTweakDecCO.PROC', kind='normal')
    reference = Cpt(EpicsSignal, 'ReferenceMO', write_pv='ReferenceMI', 
                    string=True, kind='normal')

    def __init__(self, prefix, delay_limits=(0.0, 1.0), name='DelayChannel',
                 **kwargs):
        self.low_lim = delay_limits[0]
        self.high_lim = delay_limits[1]
        super().__init__(prefix, name=name, **kwargs)

    def __call__(self, delay=None):
        """
        If DG645 instance is called with no attribute returns
        or sets current delay of channel.
        Usage
        -----
        DelayChannel()      : reads back current delay
        DelayChannel(delay) : puts value in delay()
        """
        if delay is None:
            return self.delay
        else:
            self.delay = delay

    @property
    def delay(self, value=None):
        """
        All values are in seconds. The returned values are those
        directly read off the DG645.
        If value is None:
        Returns the current delay value on the DG645 channel
        If value is not None:
        The delay value on the DG645 channel is changed to that
        value.
        """
        if value is None:
            return float(self.delay.get()[4:])
        else:
            check_DG_value(value, self.low_lim, self.high_lim)
            return self.delay.put(value)

    def tweak_delay(self, value=None, inc=False, dec=False):
        """
        If value is None:
        Returns tweak delay value on DG645 channel
        If value is not None:
        Sets tweak delay value to set value
        To tweak increase: tweak_delay(inc=True)
        To tweak decrease: tweak_delay(dec=True)
        """
        if value is not None:
            check_DG_value(value, self.low_lim, self.high_lim)
            self.delay_tweak.put(value)

        if inc:
            self.delay_inc.put(1)
        if dec:
            self.delay_dec.put(1)

        print(f'tweak val = {self.delay_tweak.get()}')
        print(f'new delay = {self.delay}')

    @property
    def MO(self):
        """
        10 MHz output to synchronize external instrumentation to DG645
        """
        return self.ref_MO.get()

    @MO.setter
    def MO(self, channel):
        self.ref_MO.put(channel)

    @property
    def MI(self):
        """
        10 MHz input to synchronize DG645 internal clock to external reference
        """
        return self.ref_MI.get()

    @MI.setter
    def MI(self, channel):
        self.ref_MI.put(channel)

    def mvr_delay(self, delta):
        """
        Moves the delay by delta relative to the current delay.
        """
        self.delay = delta + self.delay


class PulseChannel(Device):
    """
    Class that defines an output (pulse) channel of a DG645 delay generator.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG pulse channel, i.e 'MEC:LAS:DDG:01:ab'

    name : ``str``
        Alias for the delay generator channel

    amp_limits : ``tuple``, optional
        Limits on the allowed amplitude in volts. By default, the
        limits are set to (0.0, 5.0).

    off_limits : ``tuple``, optional
        Limits on the allowed offset in seconds. By default, the
        limits are set to (0.0, 1.0).
    """
    amp_AO = Cpt(EpicsSignal, 'OutputAmpAO')
    amp_AI = Cpt(EpicsSignalRO, 'OutputAmpAI')
    amp_tweak = Cpt(EpicsSignal, 'OutputAmpTweakAO')
    amp_inc = Cpt(EpicsSignal, 'OutputAmpTweakIncCO.PROC')
    amp_dec = Cpt(EpicsSignal, 'OutputAmpTweakDecCO.PROC')
    pol_BI = Cpt(EpicsSignalRO, 'OutputPolarityBI', string=True)
    pol_BO = Cpt(EpicsSignal, 'OutputPolarityBO', string=True)
    off_AO = Cpt(EpicsSignal, 'OutputOffsetAO')
    off_AI = Cpt(EpicsSignalRO, 'OutputOffsetAI')
    off_tweak = Cpt(EpicsSignal, 'OutputOffsetTweakAO')
    off_inc = Cpt(EpicsSignal, 'OutputOffsetTweakIncCO.PROC')
    off_dec = Cpt(EpicsSignal, 'OutputOffsetTweakDecCO.PROC')
    ttl_mode = Cpt(EpicsSignal, 'OutputModeTtlSS.PROC')
    nim_mode = Cpt(EpicsSignal, 'OutputModeNimSS.PROC')

    def __init__(self, prefix, amp_limits=(0.0, 5.0), off_limits=(0.0, 1.0),
                 name='PulseChannel', **kwargs):
        self.amp_low_lim = amp_limits[0]
        self.amp_high_lim = amp_limits[1]
        self.off_low_lim = off_limits[0]
        self.off_high_lim = off_limits[1]
        super().__init__(prefix, name=name, **kwargs)

    @property
    def polarity(self):
        """
        If value is None:
        Returns pulse channel polarity
        If value is not None:
        Sets pulse channel polarity
        "POS" or "NEG"
        """
        return self.pol_BI.get()

    @polarity.setter
    def polarity(self, value):
        self.pol_BO.put(value)

    @property
    def offset(self):
        """
        If value is None:
        Returns the current offset value on the DG645 channel
        If value is not None:
        The offset value on the DG645 channel is changed to that
        value.
        """
        return self.off_AI.get()

    @offset.setter
    def offset(self, value):
        check_DG_value(value, self.off_low_lim, self.off_high_lim)
        self.off_AO.put(value)

    def tweak_offset(self, value=None, inc=False, dec=False):
        """
        If value is None:
        Returns tweak offset value on DG645 channel
        If value is not None:
        Sets tweak delay value to set value
        To tweak increase: tweak_offset(inc=True)
        To tweak decrease: tweak_offset(dec=True)
        """
        if value is not None:
            check_DG_value(value, self.off_low_lim, self.off_high_lim)
            self.off_tweak.put(value)

        if inc:
            self.off_inc.put(1)
        if dec:
            self.off_dec.put(1)

        print(f'tweak val = {self.off_tweak.get()}')
        print(f'new offset = {self.offset}')

    def mvr_off(self, delta):
        """
        Moves the pulse offset by delta relative to the current offset.
        """
        self.offset = delta + self.offset

    @property
    def amplitude(self):
        """
        If value is None:
        Returns the current offset value on the DG645 channel
        If valueis not  None:
        The offset value on the DG645 channel is changed to that
        value.
        """
        return self.amp_AI.get()

    @amplitude.setter
    def amplitude(self, value):
        check_DG_value(value, self.amp_low_lim, self.amp_high_lim)
        self.amp_AO.put(value)

    def tweak_amplitude(self, value=None, inc=False, dec=False):
        """
        If valueis None:
        Returns tweak amplitude value on DG645 channel
        If value is not None:
        Sets tweak amplitude value to set value
        To tweak increase: tweak(inc=True)
        To tweak decrease: tweak(dec=True)
        """
        if value is not None:
            check_DG_value(value, self.amp_low_lim, self.amp_high_lim)
            self.amp_tweak.put(value)

        if inc:
            self.amp_inc.put(1)
        if dec:
            self.amp_dec.put(1)

        print(f'tweak val = {self.amp_tweak.get()}')
        print(f'new amplitude = {self.amplitude}')

    def mvr_amp(self, delta):
        """
        Moves the pulse amplitude by delta relative to the current amplitude.
        """
        self.amplitude = delta + self.amplitude

    def set_output_mode(self, value):
        """
        TTL function: offset is 0.0V amplitude step is 4.0V
        NIM function: offset is -0.8V amplitude step is 0.8V
        ---------
        Usage
        ---------
        set_output_mode('TTL')
        set_output_mode('NIM')
        """
        if value is 'TTL':
            self.ttl_mode.put(1)
        if value is 'NIM':
            self.nim_mode.put(1)


class Trigger(Device):
    """
    Class that defines an output (pulse) channel of a DG645 delay generator.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, i.e 'MEC:LAS:DDG:01'

    name : ``str``
        Alias for the delay generator triggers
    """
    trig_sourceMO = Cpt(EpicsSignal, ':triggerSourceMO', string=True)
    trig_sourceMI = Cpt(EpicsSignalRO, ':triggerSourceMI', string=True)
    trig_inhibitMO = Cpt(EpicsSignal, ':triggerInhibitMO', string=True)
    trig_inhibitMI = Cpt(EpicsSignalRO, ':triggerInhibitMI', string=True)

    def __init__(self, prefix, name='triggers', **kwargs):
        super().__init__(prefix, name=name, **kwargs)

    @property
    def trig_source(self):
        """
        If source is None, returns current trigger source,
        If source is not None, sets trigger source to user input
        source={'Ext ^edge','Ext ~edge', 'SS ext ^edge', 'SS ext ~edge',
                'Single Shot', 'Line'}
        """
        return self.trig_sourceMI.get()

    @trig_source.setter
    def trig_source(self, source):
        self.trig_sourceMO.put(source)

    @property
    def trig_inhibit(self):
        """
        If value is None, returns trigger inhibit setting
        If value is not None, sets inhibit to value
        value={'Off', 'Triggers', 'AB', 'AB,CD', 'AB,CD,EF', 'AB,CD,EF,GH'}
        """
        return self.trig_inhibitMI.get()

    @trig_inhibit.setter
    def trig_inhibit(self, value):
        self.trig_inhibitMO.put(value)


class DG645Channel(Device):
    """
    Defines a particular channel with pulse output `XY` and delay outputs
    `X` and `Y`. Set width, amplitude, polarity, reference and triggers
    for pulse. Limits can be passed as kwargs.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, e.g. 'MEC:LAS:DDG:01'

    channel : ``str``
        The pulse channel on the DG, e.g. 'AB', 'CD', etc

    refA : ``str``, optional
        Leading edge zero-time reference, typically 'T0'

    refB : ``str``, optional
        Reference channel for following edge, typically rising edge channel

    delay_limits : ``tuple``, optional

    amp_limits : ``tuple``, optional

    Usage
    ---------
    DG645Channel('MEC:LAS:DDG:01', 'AB', amp_limits=(0.0, 3.0) )
    """
    amp_channel = FCpt(PulseChannel, '{self._amp_prefix}')
    delay_channel = FCpt(DelayChannel, '{self._delay_prefix}')
    width_channel = FCpt(DelayChannel, '{self._width_prefix}')
    trig_channel = FCpt(Trigger, '{self._trig_prefix}')

    def __init__(self, prefix, channel, refA='T0', refB=None, name='DGChannel',
                 **kwargs):
        self._amp_prefix = f'{prefix}:{channel.lower()}'
        self._delay_prefix = f'{prefix}:{channel[0].lower()}'
        self._width_prefix = f'{prefix}:{channel[1].lower()}'
        self._trig_prefix = f'{prefix}'
        super().__init__(prefix, name=name, **kwargs)

        self.delay_channel.MO = refA
        if refB is None:
            self.width_channel.MO = channel[0].upper()
        else:
            self.width_channel.MO = refB

    def delay(self, val=None):
        if val is None:
            return self.delay_channel.delay
        else:
            self.delay_channel.delay = val

    def width(self, val=None):
        if val is None:
            return self.width_channel.delay
        else:
            self.width_channel.delay = val

    def amplitude(self, val=None):
        if val is None:
            return self.amp_channel.amplitude
        else:
            self.amp_channel.amplitude = val

    def polarity(self, val=None):
        if val is None:
            return self.amp_channel.polarity
        else:
            self.amp_channel.polarity = val

    def power(self, val):
        # ON/OFF
        if val == 'ON':
            self.amplitude(4.0)
        elif val == 'OFF':
            self.amplitude(0.0)

    def trig_source(self, val=None):
        if val is None:
            return self.trig_channel.trig_source
        else:
            self.trig_channel.trig_source = val

    def trig_inhib(self, val=None):
        if val is None:
            return self.trig_channel.trig_inhibit
        else:
            self.trig_channel.trig_inhibit = val


class DG645(Device):
    """
    Class to create complete DG645 device with access to
    all pulse and delay channels of the delay generator.
    """
    chAB = FCpt(DG645Channel, '{self.prefix}', channel='AB')
    chCD = FCpt(DG645Channel, '{self.prefix}', channel='CD')
    chEF = FCpt(DG645Channel, '{self.prefix}', channel='EF')
    chGH = FCpt(DG645Channel, '{self.prefix}', channel='GH')

    def __init__(self, prefix, name='dg645', **kwargs):
        self.prefix = prefix
        super().__init__(prefix, name=name, **kwargs)


def check_DG_value(value, low_lim, high_lim):
    """
    Raises an exception if the DG is being given a delay or offset
    which is outside the allowed limits either default or user set.
    """
    if not (low_lim <= value <= high_lim):
        raise LimitError("Value {} outside of range [{}, {}]"
                         .format(value, low_lim, high_lim))
