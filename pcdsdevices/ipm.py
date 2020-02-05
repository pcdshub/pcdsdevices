"""
Module for the `IPM` intensity position monitor class
"""
import shutil
import os
from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal
from .doc_stubs import basic_positioner_init, insert_remove, IPM_base
from .inout import InOutRecordPositioner
from .epics_motor import IMS
from .evr import Trigger


class IPMTarget(InOutRecordPositioner):
    """
    Target of a standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves
    the target position to any of the four set positions, or out. Valid states
    are (1, 2, 3, 4, 5) or the equivalent
    (TARGET1, TARGET2, TARGET3, TARGET4, OUT).
    """
    __doc__ += basic_positioner_init

    in_states = ['TARGET1', 'TARGET2', 'TARGET3', 'TARGET4']
    states_list = in_states + ['OUT']

    # Assume that having any target in gives transmission 0.8
    _transmission = {st: 0.8 for st in in_states}


class IPMDiode(Device):
    """
    Diode of a standard intensity position monitor.

    This device has members for x and y motors, where x-motion is set up as an
    IMS motor and y-motion is an InOutRecordPositioner that moves the diode
    position to any of the four set positions, or out. There is also a member,
    y, which points to the motor of the y-motion.
    """

    x = FCpt(IMS, '{self.x_prefix}', kind='normal')
    state = Cpt(InOutRecordPositioner, '', kind='normal')

    def __init__(self, prefix, *, name,  **kwargs):
        self.x_prefix = 'XMOTOR'
        super().__init__(prefix, name=name, **kwargs)
        self.y = self.state.motor


class IPMMotion(Device):
    """
    Standard intensity position monitor.

    This contains two state devices, a target and a diode.
    """
    target = Cpt(IPMTarget, ':TARGET', kind='normal')
    diode = Cpt(IPMDiode, ':DIODE', kind='omitted')

    # QIcon for UX
    _icon = 'ei.screenshot'

    tab_whitelist = ['target', 'diode']

    @property
    def inserted(self):
        """Returns ``True`` if target is inserted. Diode never blocks."""
        return self.target.inserted

    @property
    def removed(self):
        """Returns ``True`` if target is removed. Diode never blocks."""
        return self.target.removed

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the target out of the beam. Diode never blocks."""
        return self.target.remove(moved_cb=moved_cb,
                                  timeout=timeout,
                                  wait=wait)

    remove.__doc__ += insert_remove

    @property
    def transmission(self):
        """Returns the target's transmission value. Diode never blocks."""
        return self.target.transmission


class IPIMBChannel(Device):
    """
    Class for a single channel read out by an ipimb box

    Parameters
    ----------
    prefix : ``str``
        Ipimb base PV

    name : ``str``
        Alias for the ipimb box

    channnel_index : ``int``
        Index for gauge (0-3)
    """
    amplitude = FCpt(EpicsSignal, '{self.prefix}:CH{self.channel_index}',
                     kind='hinted')
    gain = FCpt(EpicsSignal,
                '{self.prefix}:ChargeAmpRangeCH{self.channel_index}',
                kind='config', string=True)

    base = FCpt(EpicsSignal, '{self.prefix}:CH{self.channel_index}_BASE',
                kind='config')
    scale = FCpt(EpicsSignal, '{self.prefix}:CH{self.channel_index}_SCALE',
                 kind='config')

    def __init__(self, prefix, *, name, channel_index,  **kwargs):
        self.channel_index = channel_index
        super().__init__(prefix, name=name, **kwargs)


class IPIMB(Device):
    """
    Class for an ipimb box.

    Parameters
    ----------
    prefix : ``str``
        Ipimb base PV

    name : ``str``
        Alias for the ipimb

    prefix_ioc : ``str``
        Ipimb base PV for IOC PVs

    Components - readback:
    total sum of all 4 channels (i0 if stadard IPM device)
    x&y beam position position calculated from 4 channels
    Components - configuration:
    bias: voltage aplied to diodes in V
    delay: delay of trigger relative to input EVR
    trigger:
    """
    isum = Cpt(EpicsSignal, ':SUM', kind='hinted')
    xpos = Cpt(EpicsSignal, ':XPOS', kind='normal')
    ypos = Cpt(EpicsSignal, ':YPOS', kind='normal')
    evr_channel = Cpt(Trigger, ':TRIG:TRIG0', kind='normal')
    delay = Cpt(EpicsSignal, ':TrigDelay', kind='config')
    bias = Cpt(EpicsSignal, ':DiodeBias', kind='config')
    ch0 = FCpt(IPIMBChannel, '{self.prefix}', channel_index=0, kind='normal')
    ch1 = FCpt(IPIMBChannel, '{self.prefix}', channel_index=1, kind='normal')
    ch2 = FCpt(IPIMBChannel, '{self.prefix}', channel_index=2, kind='normal')
    ch3 = FCpt(IPIMBChannel, '{self.prefix}', channel_index=3, kind='normal')

    # also be careful that you have to wait until trigger is enabled
    # again before device can be used again.
    # wait functionality?

    def __init__(self, prefix, *, name, prefix_ioc, **kwargs):
        if not prefix_ioc:
            self._prefix_ioc = 'IOC:%s' % prefix
        else:
            self._prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)

    def screen(self):
        """
        Function to call the (pyQT) screen for an IPIMB box
        """
        executable = '/reg/g/pcds/controls/pycaqt/ipimb/ipimb.py'
        if shutil.which(executable) is None:
            print('%s is not on path, we cannot start the screen' % executable)
            return
        executable += ' --dir /reg/g/pcds/controls/pycaqt/ipimb'
        os.system('%s --base %s --ioc %s --evr %s &' %
                  (executable, self.prefix, self._prefix_ioc,
                   self.prefix+':TRIG'))


class Wave8Channel(Device):
    """
    Class for a single channel read out by a wave8

    Parameters
    ----------
    prefix : ``str``
        Wave8 base PV

    name : ``str``
        Alias for the wave8

    channnel_index : ``int``
        Index for gauge (0-15)
    """

    amplitude = FCpt(EpicsSignal, '{self.prefix}:AMPL_{self.channel_index}',
                     kind='hinted')
    tpos = FCpt(EpicsSignal, '{self.prefix}:TPOS_{self.channel_index}',
                kind='normal')
    number_of_samples = FCpt(
        EpicsSignal, '{self.prefix}:NumberOfSamples{self.channel_index}_RBV',
        write_pv='{self.prefix}:NumberOfSamples{self.channel_index}',
        kind='config')
    delay = FCpt(
        EpicsSignal, '{self.prefix}:Delay{self.channel_index}', kind='config',
        write_pv='{self.prefix}:Delay{self.channel_index}_RBV')

    def __init__(self, prefix, *, name, channel_index,  **kwargs):
        self.channel_index = channel_index
        super().__init__(prefix, name=name, **kwargs)


class Wave8(Device):
    """
    Class for a wave8

    Parameters
    ----------
    prefix : ``str``
        Wave8 base PV

    name : ``str``
        Alias for the wave8
    """
    isum = Cpt(EpicsSignal, ':SUM', kind='normal')
    xpos = Cpt(EpicsSignal, ':XPOS', kind='normal')
    ypos = Cpt(EpicsSignal, ':YPOS', kind='normal')
    evr_channel = Cpt(Trigger, ':TRIG:TRIG0', kind='normal')
    ch0 = FCpt(Wave8Channel, '{self.prefix}', channel_index=0, kind='normal')
    ch1 = FCpt(Wave8Channel, '{self.prefix}', channel_index=1, kind='normal')
    ch2 = FCpt(Wave8Channel, '{self.prefix}', channel_index=2, kind='normal')
    ch3 = FCpt(Wave8Channel, '{self.prefix}', channel_index=3, kind='normal')
    ch4 = FCpt(Wave8Channel, '{self.prefix}', channel_index=4, kind='normal')
    ch5 = FCpt(Wave8Channel, '{self.prefix}', channel_index=5, kind='normal')
    ch6 = FCpt(Wave8Channel, '{self.prefix}', channel_index=6, kind='normal')
    ch7 = FCpt(Wave8Channel, '{self.prefix}', channel_index=7, kind='normal')
    ch8 = FCpt(Wave8Channel, '{self.prefix}', channel_index=8, kind='normal')
    ch9 = FCpt(Wave8Channel, '{self.prefix}', channel_index=9, kind='normal')
    ch10 = FCpt(Wave8Channel, '{self.prefix}', channel_index=10, kind='normal')
    ch11 = FCpt(Wave8Channel, '{self.prefix}', channel_index=11, kind='normal')
    ch12 = FCpt(Wave8Channel, '{self.prefix}', channel_index=12, kind='normal')
    ch13 = FCpt(Wave8Channel, '{self.prefix}', channel_index=13, kind='normal')
    ch14 = FCpt(Wave8Channel, '{self.prefix}', channel_index=14, kind='normal')
    ch15 = FCpt(Wave8Channel, '{self.prefix}', channel_index=15, kind='normal')

    def __init__(self, prefix, *, name, prefix_ioc=None, **kwargs):
        if not prefix_ioc:
            self._prefix_ioc = 'IOC:%s' % prefix
        else:
            self._prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)

    def screen(self):
        """
        Function to call the (pyQT) screen for a wave8 box
        """
        executable = '/reg/g/pcds/pyps/apps/wave8/latest/wave8'
        if shutil.which(executable) is None:
            print('%s is not on path, we cannot start the screen' % executable)
            return
        os.system('%s --base %s --ioc %s --evr %s &' %
                  (executable, self.prefix, self._prefix_ioc,
                   self.prefix+':TRIG'))


class IPM_IPIMB(IPMMotion):
    """
%s

    has a member ipimb which represents the ipimb box used for readout
    """
    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    ipimb = FCpt(IPIMB, '{self.prefix_ipimb}', prefix_ioc='{self.prefix_ioc}')

    def __init__(self, prefix, *, name, **kwargs):
        self.prefix_ipimb = kwargs.pop('prefix_ipimb')
        self.prefix_ioc = kwargs.pop('prefix_ioc', None)
        super().__init__(prefix, name=name, **kwargs)

    def isum(self):
        return self.ipimb.isum.get()

    def xpos(self):
        return self.ipimb.xpos.get()

    def ypos(self):
        return self.ipimb.ypos.get()

    def channel(self, i=0):
        # thrown an exception for an invalid channel?
        # if ( i >= 4 ): return None
        return getattr(self.ipimb, 'ch%i').amplitude.get()

    def channels(self):
        return [getattr(self.ipimb, 'ch%i').amplitude.get() for i in range(4)]


class IPM_Wave8(IPMMotion):
    """
%s

    has a member wave8 which represents the wave8 used for readout
    """
    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    wave8 = FCpt(Wave8, '{self.prefix_wave8}')

    def __init__(self, prefix, *, name, **kwargs):
        self.prefix_wave8 = kwargs.pop('prefix_wave8')
        super().__init__(prefix, name=name, **kwargs)

    def isum(self):
        return self.wave8.isum.get()

    def xpos(self):
        return self.wave8.xpos.get()

    def ypos(self):
        return self.wave8.ypos.get()

    def channel(self, i=0):
        return getattr(self.wave8, 'ch%i').amplitude.get()

    def channels(self):
        return [getattr(self.wave8, 'ch%i').amplitude.get() for i in range(16)]


def IPM(prefix, *, name, **kwargs):
    """
    Factory function for an IPM
    optional: IPIMB box or Wave8 for readout

    Parameters
    ----------
    prefix : ``str``
        Gauge base PV (up to GCC/GPI)

    name : ``str``
        Alias for the gauge set

    (optional) prefix_ipimb:
        Base PV for IPIMB box

    (optional) prefix_wave8:
        BasePV for wave8
    """

    if 'prefix_ipimb' in kwargs:
        return IPM_IPIMB(prefix, name=name,
                         prefix_ipimb=kwargs.pop('prefix_ipimb'), **kwargs)
    elif 'prefix_wave8' in kwargs:
        return IPM_Wave8(prefix, name=name,
                         prefix_wave8=kwargs.pop('prefix_wave8'), **kwargs)
    else:
        return IPMMotion(prefix, name=name)
