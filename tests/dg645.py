"""
Module for DG645 delay generator timing channel.
"""
from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal
from ophyd.utils import LimitError


class DelayChannel(Device):
    """
    Class that defines an output (delay) channel of a DG645 delay generator.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG channel, i.e 'MEC:LAS:DDG:01:a'

    name : ``str``
        Alias for the delay generator

    delay_limits : ``tuple``, optional
        Limits on the allowed delay in seconds. By default, the
        limits are set to (0.0, 1.0).
    """
    delay_pv = Cpt(EpicsSignal, 'DelaySI', write_pv='DelayAO', kind='hinted')
    delay_tweak = Cpt(EpicsSignal, 'DelayTweakAO', kind='config')
    delay_inc = Cpt(EpicsSignal, 'DelayTweakIncCO.PROC', kind='normal')
    delay_dec = Cpt(EpicsSignal, 'DelayTweakDecCO.PROC', kind='normal')
    ref_pv = Cpt(EpicsSignal, 'ReferenceMI', write_pv='ReferenceMO',
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
            return float(self.delay_pv.get()[4:])
        else:
            check_DG_value(value, self.low_lim, self.high_lim)
            return self.delay_pv.put(value)

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

    def reference(self, channel=None):
        """
        channel: ``str``
        Delay reference channel
        If channel is None:
        Returns current delay reference on selected channel
        If channel is not None:
        Sets channel as delay reference
        """
        if channel is None:
            return self.ref_pv.get()
        else:
            return self.ref_pv.put(channel)

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
    amplitude_pv = Cpt(EpicsSignal, 'OutputAmpAI', write_pv='OutputAmpAO',
                       kind='hinted')
    amplitude_tweak = Cpt(EpicsSignal, 'OutputAmpTweakAO', kind='config')
    amplitude_inc = Cpt(EpicsSignal, 'OutputAmpTweakIncCO.PROC', kind='normal')
    amplitude_dec = Cpt(EpicsSignal, 'OutputAmpTweakDecCO.PROC', kind='normal')
    pol_pv = Cpt(EpicsSignal, 'OutputPolarityBI', write_pv='OutputPolarityBO',
                 string=True, kind='config')
    offset_pv = Cpt(EpicsSignal, 'OutputOffsetAI', write_pv='OutputOffsetAO',
                    kind='hinted')
    offset_tweak = Cpt(EpicsSignal, 'OutputOffsetTweakAO', kind='config')
    offset_inc = Cpt(EpicsSignal, 'OutputOffsetTweakIncCO.PROC', kind='normal')
    offset_dec = Cpt(EpicsSignal, 'OutputOffsetTweakDecCO.PROC', kind='normal')
    ttl_mode = Cpt(EpicsSignal, 'OutputModeTtlSS.PROC', kind='config')
    nim_mode = Cpt(EpicsSignal, 'OutputModeNimSS.PROC', kind='config')

    def __init__(self, prefix, amp_limits=(0.0, 5.0), off_limits=(0.0, 1.0),
                 name='PulseChannel', **kwargs):
        self.amp_low_lim = amp_limits[0]
        self.amp_high_lim = amp_limits[1]
        self.off_low_lim = off_limits[0]
        self.off_high_lim = off_limits[1]
        super().__init__(prefix, name=name, **kwargs)

    def polarity(self, value=None):
        """
        value : ``str`` "POS" or "NEG"
        If value is None:
        Returns pulse channel polarity
        If value is not None:
        Sets pulse channel polarity
        """
        if value is None:
            return self.pol_pv.get()
        else:
            return self.pol_pv.put(value)

    def offset(self, value=None):
        """
        If value is None:
        Returns the current offset value on the DG645 channel
        If value is not None:
        The offset value on the DG645 channel is changed to that
        value.
        """
        if value is None:
            return self.offset_pv.get()
        else:
            check_DG_value(value, self.off_low_lim, self.off_high_lim)
            return self.offset_pv.put(value)

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
            self.offset_tweak.put(value)

        if inc:
            self.offset_inc.put(1)
        if dec:
            self.offset_dec.put(1)

        print(f'tweak val = {self.off_tweak.get()}')
        print(f'new offset = {self.offset}')

    def mvr_off(self, delta):
        """
        Moves the pulse offset by delta relative to the current offset.
        """
        self.offset = delta + self.offset

    def amplitude(self, value=None):
        """
        If value is None:
        Returns the current offset value on the DG645 channel
        If valueis not  None:
        The offset value on the DG645 channel is changed to that
        value.
        """
        if value is None:
            return self.amplitude_pv.get()
        else:
            check_DG_value(value, self.amp_low_lim, self.amp_high_lim)
            return self.amplitude_pv.put(value)

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
            self.amplitude_tweak.put(value)

        if inc:
            self.amplitude_inc.put(1)
        if dec:
            self.amplitude_dec.put(1)

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
    source = Cpt(EpicsSignal, ':triggerSourceMI', write_pv=':triggerSourceMO',
                 string=True, kind='normal')
    inhib = Cpt(EpicsSignal, ':triggerInhibitMI', write_pv=':triggerInhibitMO',
                string=True, kind='normal')

    def __init__(self, prefix, name='triggers', **kwargs):
        super().__init__(prefix, name=name, **kwargs)

    def trig_source(self, value):
        """
        If value is None, returns current trigger source,
        If value is not None, sets trigger source to user input
        value: ``str`` {'Ext ^edge','Ext ~edge', 'SS ext ^edge',
                         'SS ext ~edge', 'Single Shot', 'Line'}
        """
        if value is None:
            return self.source.get()
        else:
            return self.source.put(value)

    def trig_inhibit(self, value):
        """
        If value is None, returns trigger inhibit setting
        If value is not None, sets inhibit to value
        value : ``str`` {'Off', 'Triggers', 'AB', 'AB,CD',
                           'AB,CD,EF', 'AB,CD,EF,GH'}
        """
        if value is None:
            return self.inhib.get()
        else:
            return self.inhib.put(value)


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

        self.delay_channel.reference(refA)
        if refB is None:
            self.width_channel.reference(channel[0].upper())
        else:
            self.width_channel.reference(refB)

    def delay(self, val=None):
        if val is None:
            return self.delay_channel.delay()
        else:
            self.delay_channel.delay(val)

    def width(self, val=None):
        if val is None:
            return self.width_channel.delay()
        else:
            self.width_channel.delay(val)

    def amplitude(self, val=None):
        if val is None:
            return self.amp_channel.amplitude()
        else:
            self.amp_channel.amplitude(val)

    def polarity(self, val=None):
        if val is None:
            return self.amp_channel.polarity()
        else:
            self.amp_channel.polarity(val)

    def status(self, val):
        # ON/OFF
        if val == 'ON':
            self.amplitude(4.0)
        elif val == 'OFF':
            self.amplitude(0.0)

    def trig_source(self, val=None):
        if val is None:
            return self.trig_channel.trig_source()
        else:
            self.trig_channel.trig_source(val)

    def trig_inhib(self, val=None):
        if val is None:
            return self.trig_channel.trig_inhibit()
        else:
            self.trig_channel.trig_inhibit(val)


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
