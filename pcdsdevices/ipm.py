"""
Module for the `IPM` intensity position monitor class
"""
from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal
from .doc_stubs import basic_positioner_init, insert_remove, IPM_base
from .inout import InOutRecordPositioner
from .epics_motor import IMS
from .evr import Trigger
from .utils import ipm_screen


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

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.y_motor = self.motor


class IPMDiode(Device):
    """
    Diode of a standard intensity position monitor.

    This device has members for x and y motors, where x-motion is set up as an
    IMS motor and y-motion is an InOutRecordPositioner that moves the diode
    position to any of the four set positions, or out. There is also a member,
    y, which points to the motor of the y-motion.
    """

    tab_whitelist = ['x_motor', 'y_motor', 'insert', 'remove']

    x_motor = FCpt(IMS, '{self.x_prefix}', kind='normal')
    state = Cpt(InOutRecordPositioner, '', kind='normal')

    def __init__(self, prefix, *, name,  **kwargs):
        self.x_prefix = 'XMOTOR'
        super().__init__(prefix, name=name, **kwargs)
        self.y_motor = self.state.motor

    @property
    def inserted(self):
        """Returns ``True`` if diode is inserted."""
        return self.state.inserted

    @property
    def removed(self):
        """Returns ``True`` if diode is removed."""
        return self.state.removed

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode into the beam."""
        return self.state.insert(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode out of the beam."""
        return self.state.remove(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    remove.__doc__ += insert_remove


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
        """Returns ``True`` if target is inserted."""
        return self.target.inserted

    @property
    def removed(self):
        return self.target.removed
        """Returns ``True`` if target is removed. Diode does not block
           when inserted or removed"""

    @property
    def transmission(self):
        """Returns the target's transmission value."""
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
    ch0 = Cpt(IPIMBChannel, '', channel_index=0, kind='normal')
    ch1 = Cpt(IPIMBChannel, '', channel_index=1, kind='normal')
    ch2 = Cpt(IPIMBChannel, '', channel_index=2, kind='normal')
    ch3 = Cpt(IPIMBChannel, '', channel_index=3, kind='normal')

    def __init__(self, prefix, *, name, prefix_ioc=None, **kwargs):
        if not prefix_ioc:
            self._prefix_ioc = 'IOC:%s' % prefix
        else:
            self._prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)

    def screen(self):
        """Function to call the (pyQT) screen for an IPIMB box"""
        return ipm_screen('IPIMB', self._prefix, self._prefix_ioc)


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
    ch0 = Cpt(Wave8Channel, '', channel_index=0, kind='normal')
    ch1 = Cpt(Wave8Channel, '', channel_index=1, kind='normal')
    ch2 = Cpt(Wave8Channel, '', channel_index=2, kind='normal')
    ch3 = Cpt(Wave8Channel, '', channel_index=3, kind='normal')
    ch4 = Cpt(Wave8Channel, '', channel_index=4, kind='normal')
    ch5 = Cpt(Wave8Channel, '', channel_index=5, kind='normal')
    ch6 = Cpt(Wave8Channel, '', channel_index=6, kind='normal')
    ch7 = Cpt(Wave8Channel, '', channel_index=7, kind='normal')
    ch8 = Cpt(Wave8Channel, '', channel_index=8, kind='normal')
    ch9 = Cpt(Wave8Channel, '', channel_index=9, kind='normal')
    ch10 = Cpt(Wave8Channel, '', channel_index=10, kind='normal')
    ch11 = Cpt(Wave8Channel, '', channel_index=11, kind='normal')
    ch12 = Cpt(Wave8Channel, '', channel_index=12, kind='normal')
    ch13 = Cpt(Wave8Channel, '', channel_index=13, kind='normal')
    ch14 = Cpt(Wave8Channel, '', channel_index=14, kind='normal')
    ch15 = Cpt(Wave8Channel, '', channel_index=15, kind='normal')

    def __init__(self, prefix, *, name, prefix_ioc=None, **kwargs):
        if not prefix_ioc:
            self._prefix_ioc = 'IOC:%s' % prefix
        else:
            self._prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)

    def screen(self):
        """Function to call the (pyQT) screen for a Wave8 box"""
        return ipm_screen('Wave8', self._prefix, self._prefix_ioc)


class IPM_Det():
    """
    Base class for IPM_IPIMB and IPM_Wave8. Not meant to be instantiated.
    """

    def isum(self):
        """Returns the detector's isum value."""
        return self.det.isum.get()

    def xpos(self):
        """Returns the detector's xpos value."""
        return self.det.xpos.get()

    def ypos(self):
        """Returns the detector's ypos value."""
        return self.det.ypos.get()

    def channel(self, i=0):
        """Returns the detector's specified channel"""
        if (i >= self._num_channels or i < 0):
            raise ValueError("Invalid channel number!")
        else:
            return getattr(self.det, 'ch%d' % i).amplitude.get()

    def channels(self):
        """Returns a dictionary of all of the detector's channels"""
        return [getattr(self.det, 'ch%d' % i).amplitude.get()
                for i in range(self._num_channels)]


class IPM_IPIMB(IPMMotion, IPM_Det):
    """
%s

    has a member ipimb which represents the ipimb box used for readout
    """
    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    ipimb = FCpt(IPIMB, '{self.prefix_ipimb}', prefix_ioc='{self.prefix_ioc}')

    # IPIMB's have four channels
    _num_channels = 4

    def __init__(self, prefix, *, name, **kwargs):
        self.prefix_ipimb = kwargs.pop('prefix_ipimb')
        self.prefix_ioc = kwargs.pop('prefix_ioc', None)
        super().__init__(prefix, name=name, **kwargs)
        self.det = self.ipimb


class IPM_Wave8(IPMMotion, IPM_Det):
    """
%s

    has a member wave8 which represents the wave8 used for readout
    """
    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    wave8 = FCpt(Wave8, '{self.prefix_wave8}', prefix_ioc='{self.prefix_ioc}')

    # Wave8's have sixteen channels
    _num_channels = 16

    def __init__(self, prefix, *, name, **kwargs):
        self.prefix_wave8 = kwargs.pop('prefix_wave8')
        self.prefix_ioc = kwargs.pop('prefix_ioc', None)
        super().__init__(prefix, name=name, **kwargs)
        self.det = self.wave8


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
