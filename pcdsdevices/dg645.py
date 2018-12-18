"""
Module for DG645 delay generator timing channel.
"""
from ophyd.device import Device, Component as Cpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.utils import LimitError


class DG645(object):
    """
    Class to access all channels of DG645 delay generator
    """
    def __init__(self, prefix, name='dg645', **kwargs):
        self.chAB = DG645Channel(prefix, 'AB')
        self.chCD = DG645Channel(prefix, 'CD')
        self.chEF = DG645Channel(prefix, 'EF')
        self.chGH = DG645Channel(prefix, 'GH')


class DG645Channel(object):
    """
    Defines a particular channel with pulse output `XY` and delay outputs
    `X` and `Y`. Set width, amplitude, polarity, reference and triggers 
    for pulse. Limits can be passed as kwargs.

    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, e.g. 'MEC:LAS:DDG:01:'
    
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
    DG645Channel('MEC:LAS:DDG:01:', 'AB', amp_limits=(0.0, 3.0) )
    """
    
    def __init__(self, prefix, channel, refA='T0', refB=None, **kwargs):
        self.ampCh   = pulseChannel(prefix, channel, **kwargs)
        self.delayCh = delayChannel(prefix, channel[0], **kwargs)
        self.widthCh = delayChannel(prefix, channel[1], **kwargs)
        self.delayCh.MO = refA
        if refB is None: self.widthCh.MO = channel[0].upper()
        else: self.widthCh.MO = refB
        self.trigCh = trigger(prefix)
        
    def delay(self, val=None):
        if val is None:
            return self.delayCh.delay
        else:
            self.delayCh.delay=val

    def width(self, val=None):
        if val is None:
            return self.widthCh.delay
        else:
            self.widthCh.delay=val

    def amplitude(self, val=None):
        if val is None:
            return self.ampCh.amplitude
        else:
            self.ampCh.amplitude=val

    def polarity(self, val=None):
        if val is None:
            return self.ampCh.polarity
        else:
            self.ampCh.polarity=val

    def power(self, val):
        #ON/OFF
        if val=='ON':
            self.amplitude(4.0)
        elif val=='OFF':
            self.amplitude(0.0)

    def trig_source(self, val=None):
        if val is None:
            return self.trigCh.trig_source
        else:
            self.trigCh.trig_source=val

    def trig_inhib(self, val=None):
        if val is None:
            return self.trigCh.trig_inhibit
        else:
            self.trigCh.trig_inhibit=val


class delayChannel(Device):
    """
    Class that defines an output (delay) channel of a DG645 delay generator.
    
    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, i.e 'MEC:LAS:DDG:01:'
    
    channel : ``str``
        The delay channel on the DG, i.e. 'a', 'g', etc

    name : ``str``                                                               
        Alias for the delay generator
    
    delay_limits : ``tuple``, optional
        Limits on the allowed delay in seconds. By default, the
        limits are set to (0.0, 1.0).
    """
    delay_AO    = Cpt(EpicsSignal, 'DelayAO')
    delay_SI    = Cpt(EpicsSignalRO,'DelaySI')
    delay_Tweak = Cpt(EpicsSignal, 'DelayTweakAO')
    delay_Inc   = Cpt(EpicsSignal, 'DelayTweakIncCO.PROC')
    delay_Dec   = Cpt(EpicsSignal, 'DelayTweakDecCO.PROC')
    ref_MI      = Cpt(EpicsSignal, 'ReferenceMI')
    ref_MO      = Cpt(EpicsSignal, 'ReferenceMO')
    
    def __init__(self, prefix, channel, delay_limits=(0.0, 1.0), name='DelayChannel', **kwargs):
        self.low_lim = delay_limits[0]
        self.high_lim = delay_limits[1]
        self.channel = channel
        self.__refsDict = {"T0":0, "A":1, "B":2, "C":3, "D":4, "E":5, "F":6, 
                           "G":7, "H":8}
        self.__refsDictInv = {0:"T0", 1:"A", 2:"B", 3:"C", 4:"D", 5:"E", 6:"F", 
                              7:"G", 8:"H"}
        super().__init__(prefix=prefix+channel.lower(), name=name)
        
    def __call__(self, delay=None):
        """
        If DG645 instance is called with no attribute returns
        or sets current delay of channel.
        Usage
        -----
        dg645()      : reads back current delay
        dg645(delay) : puts value in delay()
        """
        if delay is None:
            return self.delay
        else:
            self.delay = delay
            
    @property
    def delay(self):
        """
        All values are in seconds. The returned values are those
        directly read off the DG645.
        If value is None:
        Returns the current delay value on the DG645 channel
        If value is not None:
        The delay value on the DG645 channel is changed to that
        value.        
        """
        return float(self.delay_SI.get()[4:])
        
    @delay.setter
    def delay(self, value):
        checkValue(value, self.low_lim, self.high_lim)
        self.delay_AO.put(value)
        
    def tweak(self, value=None, inc=False, dec=False):
        """
        If value is None:
        Returns tweak delay value on DG645 channel
        If value is not None:
        Sets tweak delay value to set value 
        To tweak increase: tweak(inc=True)
        To tweak decrease: tweak(dec=True)
        """
        if value is None:
            return self.delay_Tweak.get()

        else:
            DG645.checkValue(value, self.low_lim, self.high_lim)
            self.delay_Tweak.put(value)
            
        if inc:
            self.delay_Inc.put(1)
        if dec:
            self.delay_Dec.put(1)
        
    @property
    def MO(self):
        """
        10 MHz output to synchronize external instrumentation to DG645
        """
        return self.__refsDictInv[self.ref_MO.get()]
    
    @MO.setter
    def MO(self, channel):
        self.ref_MO.put(self.__refsDict[channel])
        
    @property
    def MI(self):
        """
        10 MHz input to synchronize DG645 internal clock to external reference 
        """
        return self.__refsDictInv[self.ref_MI.get()]
        
    @MI.setter
    def MI(self, channel):
        self.ref_MI.put(self.__refsDict[channel])
        
    def mvr_delay(self, delta):
        """
        Moves the delay by delta relative to the current delay.
        """
        self.delay = delta + self.delay


class pulseChannel(Device):
    """
    Class that defines an output (pulse) channel of a DG645 delay generator.
    
    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG pulse channel, i.e 'MEC:LAS:DDG:01:'

    channel : ``str``
        The pulse channel on the DG, i.e. 'ab', 'gh', etc
    
    name : ``str``                                                               
        Alias for the delay generator channel
    
    amp_limits : ``tuple``, optional                                                 
        Limits on the allowed amplitude in volts. By default, the
        limits are set to (0.0, 5.0).
    
    off_limits : ``tuple``, optional                                                 
        Limits on the allowed offset in seconds. By default, the
        limits are set to (0.0, 1.0).
    """
    amp_AO    = Cpt(EpicsSignal, 'OutputAmpAO')
    amp_AI    = Cpt(EpicsSignalRO, 'OutputAmpAI')
    amp_Tweak = Cpt(EpicsSignal, 'OutputAmpTweakAO')
    amp_Inc   = Cpt(EpicsSignal, 'OutputAmpTweakIncCO.PROC')
    amp_Dec   = Cpt(EpicsSignal, 'OutputAmpTweakDecCO.PROC')
    pol_BI    = Cpt(EpicsSignalRO, 'OutputPolarityBI')
    pol_BO    = Cpt(EpicsSignal, 'OutputPolarityBO')
    off_AO    = Cpt(EpicsSignal, 'OutputOffsetAO')
    off_AI    = Cpt(EpicsSignalRO, 'OutputOffsetAI')
    off_Tweak = Cpt(EpicsSignal, 'OutputOffsetTweakAO')
    off_Inc   = Cpt(EpicsSignal, 'OutputOffsetTweakIncCO.PROC')
    off_Dec   = Cpt(EpicsSignal, 'OutputOffsetTweakDecCO.PROC')
    
    
    def __init__(self, prefix, channel, amp_limits=(0.0,5.0), off_limits=(0.0, 1.0), name='PulseChannel', **kwargs):
        self.amp_low_lim = amp_limits[0]
        self.amp_high_lim = amp_limits[1]
        self.off_low_lim = off_limits[0]
        self.off_high_lim = off_limits[1]
        self.__polDict = {'NEG':0, 'POS':1}
        self.__polDictInv = {0:'NEG', 1:'POS'}
        super().__init__(prefix=prefix+channel.lower(), name=name)
            

    @property
    def polarity(self):
        """
        If value is None:
        Returns pulse channel polarity
        If value is not None:
        Sets pulse channel polarity
        """
        return self.__polDictInv[self.pol_BI.get()]

    @polarity.setter
    def polarity(self, value):
        self.pol_BO.put(self.__polDict[value])
        

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
        checkValue(value, self.off_low_lim, self.off_high_lim)
        self.off_AO.put(value)
        
            
    def tweak_offset(self, value=None, inc=False, dec=False):
        """
        If value is None:
        Returns tweak offset value on DG645 channel
        If value is not None:
        Sets tweak delay value to set value 
        To tweak increase: tweak(inc=True)
        To tweak decrease: tweak(dec=True)
        """
        if value is None:
            return self.off_Tweak.get()
        else:
            checkValue(value, self.off_low_lim, self.off_high_lim)
            self.off_Tweak.put(value)
            
        if inc:
            self.off_Inc.put(1)
        if dec:
            self.off_Dec.put(1)
        

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
        checkValue(value, self.amp_low_lim, self.amp_high_lim)
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
        if value is None:
            return self.amp_Tweak.get()
        else:
            checkValue(value, self.amp_low_lim, self.amp_high_lim)
            self.amp_Tweak.put(value)
            
        if inc:
            self.amp_Inc.put(1)
        if dec:
            self.amp_Dec.put(1)
                

    def mvr_amp(self, delta):
        """
        Moves the pulse amplitude by delta relative to the current amplitude.
        """
        self.amplitude = delta + self.amplitude



class trigger(Device):
    """
    Class that defines an output (pulse) channel of a DG645 delay generator.
    
    Parameters
    ---------
    prefix : ``str``
        The PV base of the relevant DG, i.e 'MEC:LAS:DDG:01:'
    
    name : ``str``                                                               
        Alias for the delay generator triggers
    """
    trig_sourceMO  = Cpt(EpicsSignal, 'triggerSourceMO')
    trig_sourceMI  = Cpt(EpicsSignalRO, 'triggerSourceMI')
    trig_inhibMO   = Cpt(EpicsSignal, 'triggerInhibitMO')
    trig_inhibMI   = Cpt(EpicsSignalRO, 'triggerInhibitMI')
    
    def __init__(self, prefix, name='triggers', **kwargs):
        self.__sourceDict = {"Internal":0, "Ext ^edge":1, "Ext ~edge":2, 
                             "SS ext ^edge":3, "SS ext ~edge":4, "Single Shot":5,
                             "Line":6}
        self.__sourceDictInv = {0:"Internal", 1:"Ext ^edge", 2:"Ext ~edge", 
                                3:"SS ext ^edge",4:"SS ext ~edge", 5:"Single Shot",
                                6:"Line"}
        self.__inhibDict = {"Off":0, "Triggers":1, "AB":2, "AB,CD":3, "AB,CD,EF":4,
                            "AB,CD,EF,GH":5}
        self.__inhibDictInv = {0:"Off", 1:"Triggers", 2:"AB", 3:"AB,CD", 
                               4:"AB,CD,EF", 5:"AB,CD,EF,GH"}


        super().__init__(prefix=prefix, name=name)
            

    @property
    def trig_source(self):
        """
        If source is None, returns current trigger source,
        If source is not None, sets trigger source to user input
        source={'Ext ^edge','Ext ~edge', 'SS ext ^edge', 'SS ext ~edge',
                'Single Shot', 'Line'}
        """
        return self.__sourceDictInv[self.trig_sourceMI.get()]

    @trig_source.setter
    def trig_source(self, source):
        self.trig_sourceMO.put(self.__sourceDict[source])

    
    @property
    def trig_inhibit(self):
        """
        If value is None, returns trigger inhibit setting
        If value is not None, sets inhibit to value
        value={'Off', 'Triggers', 'AB', 'AB,CD', 'AB,CD,EF', 'AB,CD,EF,GH'}
        """
        return self.__inhibDictInv[self.trig_inhibMI.get()]

    @trig_inhibit.setter
    def trig_inhibit(self, value):
        self.trig_inhibMO.put(self.__inhibDict[value])






def checkValue(value, low_lim, high_lim):
    """
    Raises an exception if the DG is being given a delay or offset
    which is outside the allowed limits either default or user set.
    """
    if not (low_lim <= value <= high_lim):
        raise LimitError("Value {} outside of range [{}, {}]"
                         .format(value, low_lim, high_lim))
