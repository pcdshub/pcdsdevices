"""
Module for the `IPM` intensity position monitor classes.
"""
import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .doc_stubs import IPM_base, basic_positioner_init, insert_remove
from .epics_motor import IMS
from .evr import Trigger
from .inout import InOutRecordPositioner
from .interface import BaseInterface
from .utils import get_status_float, get_status_value, ipm_screen

logger = logging.getLogger(__name__)


class IPMTarget(InOutRecordPositioner):
    """
    Target of a standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves the target position to any
    of the four set positions, or out. Valid states are (1, 2, 3, 4, 5) or the
    equivalent (TARGET1, TARGET2, TARGET3, TARGET4, OUT).
    """

    __doc__ += basic_positioner_init

    in_states = ['TARGET1', 'TARGET2', 'TARGET3', 'TARGET4']
    states_list = in_states + ['OUT']

    t1_composition = Cpt(EpicsSignalRO, ':TARGET1.DESC', kind='omitted')
    t2_composition = Cpt(EpicsSignalRO, ':TARGET2.DESC', kind='omitted')
    t3_composition = Cpt(EpicsSignalRO, ':TARGET3.DESC', kind='omitted')
    t4_composition = Cpt(EpicsSignalRO, ':TARGET4.DESC', kind='omitted')

    # Assume that having any target in gives transmission 0.8
    _transmission = {st: 0.8 for st in in_states}

    def get_composition(self):
        """
        Get the target composition.

        Each state is a different target with different material/thicknesses.

        Returns
        -------
        composition : str
            Composition of target.
        """
        current_state = self.state.get()
        if current_state == 1:
            return self.t1_composition.get()
        elif current_state == 2:
            return self.t2_composition.get()
        elif current_state == 3:
            return self.t3_composition.get()
        elif current_state == 4:
            return self.t4_composition.get()
        else:
            return None

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.y_motor = self.motor


class IPMDiode(BaseInterface, Device):
    """
    Diode of a standard intensity position monitor.

    This device has members for x and y motors, where x-motion is set up as an
    IMS motor and y-motion is an InOutRecordPositioner that moves the diode
    position to any of the four set positions, or out. There is also a member,
    y, which points to the motor of the y-motion.
    """

    tab_whitelist = ['x_motor', 'y_motor', 'insert', 'remove']

    x_motor = Cpt(IMS, ':X_MOTOR', kind='normal')
    state = Cpt(InOutRecordPositioner, '', kind='normal')

    def __init__(self, prefix, *, name,  **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.y_motor = self.state.motor

    @property
    def inserted(self):
        """Returns `True` if diode is inserted."""
        return self.state.inserted

    @property
    def removed(self):
        """Returns `True` if diode is removed."""
        return self.state.removed

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode into the beam."""
        return self.state.insert(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode out of the beam."""
        return self.state.remove(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    @property
    def transmission(self):
        """Returns 0 if in an unknown state. Returns 1 otherwise."""
        if self.inserted or self.removed:
            return 1
        else:
            return 0

    remove.__doc__ += insert_remove


class IPMMotion(BaseInterface, Device):
    """
    Standard intensity position monitor.

    This contains two state devices, a target and a diode.
    """

    target = Cpt(IPMTarget, ':TARGET', kind='normal')
    diode = Cpt(IPMDiode, ':DIODE', kind='normal')

    # QIcon for UX
    _icon = 'ei.screenshot'

    tab_whitelist = ['target', 'diode', 'insert', 'remove', 'inserted',
                     'removed']

    def format_status_info(self, status_info):
        """
        Override status info handler to render the ipm.

        Display ipm status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.
        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        name = ' '.join(self.prefix.split(':'))

        x_motor_pos = get_status_float(status_info, 'diode', 'x_motor',
                                       'position')
        y_motor_pos = get_status_float(status_info, 'diode', 'state', 'motor',
                                       'position')
        d_units = get_status_value(status_info, 'diode', 'x_motor',
                                   'user_setpoint', 'units')
        target_pos = get_status_value(status_info, 'target', 'motor',
                                      'position')
        t_units = get_status_value(status_info, 'target', 'motor',
                                   'user_setpoint', 'units')
        target_state_num = get_status_value(status_info, 'target',
                                            'state', 'value')
        target_state = get_status_value(status_info, 'target', 'position')

        composition = self.target.get_composition() or ''

        if 'ipimb' in status_info.keys():
            diode_type = 'IPIMB '
        elif 'wave8' in status_info.keys():
            diode_type = 'Wave8 '
        else:
            diode_type = ''

        return f"""\
{name}: Target {target_state_num} {target_state} [{composition}]
Target Position: {target_pos} [{t_units}]
{diode_type}Diode Position(x, y): \
{x_motor_pos}, {y_motor_pos} [{d_units}]
"""

    @property
    def inserted(self):
        """Returns `True` if target is inserted."""
        return self.target.inserted and self.diode.inserted

    @property
    def removed(self):
        """
        Returns `True` if target is removed and diode is not blocking.
        Diode does not block when inserted or removed.
        """
        return (self.target.removed and
                (self.diode.removed or self.diode.inserted))

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """Move both the target and diode in."""
        return (self.target.insert(moved_cb=moved_cb, timeout=timeout,
                                   wait=wait)
                & self.diode.insert(moved_cb=moved_cb, timeout=timeout,
                                    wait=wait))

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """
        Moves the target out of the beam and removes the diode if it is in an
        unknown state.
        """
        rmstatus = self.target.remove(moved_cb=moved_cb, timeout=timeout,
                                      wait=wait)
        if (self.diode.removed or self.diode.inserted):
            return rmstatus
        else:
            return (rmstatus & self.diode.remove(moved_cb=moved_cb,
                                                 timeout=timeout, wait=wait))

    def target_in(self, target_num, moved_cb=None, timeout=None, wait=False):
        """
        Moves the target to one of the target positions. There are 4 targets
        with different thickness and absorption/signal.
        The targets move vertically. To drive them in, use presets:
        ipm.target_in(x), where x = target number

        Parameters
        -----------
        target: int
            Number of which target to move in.
            Must be one of the valid target states: 1-4 or out: 5
            (TARGET1, TARGET2, TARGET3, TARGET4, OUT) respectively

        moved_cb : callable, optional
            Function to be run when the operation finishes. This callback
            should not expect any arguments or keywords.

        timeout : float, optional
            Maximum time for the motion. If `None` is given, the default value
            of this positioner is used.

        wait : bool
            If `True`, block until move is completed.

        Returns
        -------
        status: MoveStatus
        """
        return self.target.move(target_num, moved_cb=moved_cb,
                                timeout=timeout, wait=wait)

    @property
    def transmission(self):
        """Returns the combined transmission value of the target and diode."""
        return self.target.transmission * self.diode.transmission


class IPIMBChannel(BaseInterface, Device):
    """
    Class for a single channel read out by an IPIMB box.

    Parameters
    ----------
    prefix : str
        IPIMB base PV.

    name : str
        Alias for the IPIMB box.

    channnel_index : int
        Index for gauge (0-3).
    """

    tab_component_names = True

    amplitude = FCpt(EpicsSignalRO, '{self.prefix}:CH{self.channel_index}',
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


class IPIMB(BaseInterface, Device):
    """
    Class for an IPIMB box.

    Parameters
    ----------
    prefix : str
        IPIMB base PV.

    name : str
        Alias for the IPIMB.

    prefix_ioc : str
        IPIMB base PV for IOC PVs.

    Attributes
    ----------
    isum
        Total sum of all 4 channels (i0 if standard IPM device).

    xpos, ypos
        X&Y beam position position calculated from 4 channels.

    bias
        Voltage applied to diodes in V.

    delay
        Delay of trigger relative to input EVR.

    evr_channel
        Trigger component.
    """

    tab_whitelist = ['isum', 'xpos', 'ypos']

    isum = Cpt(EpicsSignalRO, ':SUM', kind='hinted')
    xpos = Cpt(EpicsSignalRO, ':XPOS', kind='normal')
    ypos = Cpt(EpicsSignalRO, ':YPOS', kind='normal')
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
        """Function to call the (pyQT) screen for an IPIMB box."""
        return ipm_screen('IPIMB', self._prefix, self._prefix_ioc)


class Wave8Channel(BaseInterface, Device):
    """
    Class for a single channel read out by a wave8.

    Parameters
    ----------
    prefix : str
        Wave8 base PV.

    name : str
        Alias for the wave8.

    channnel_index : int
        Index for gauge (0-15).
    """

    tab_component_names = True

    amplitude = FCpt(EpicsSignalRO, '{self.prefix}:AMPL_{self.channel_index}',
                     kind='hinted')
    tpos = FCpt(EpicsSignalRO, '{self.prefix}:TPOS_{self.channel_index}',
                kind='normal')
    number_of_samples = FCpt(
        EpicsSignal, '{self.prefix}:NumberOfSamples{self.channel_index}_RBV',
        write_pv='{self.prefix}:NumberOfSamples{self.channel_index}',
        kind='config')
    delay = FCpt(
        EpicsSignal, '{self.prefix}:Delay{self.channel_index}_RBV',
        write_pv='{self.prefix}:Delay{self.channel_index}', kind='config')

    def __init__(self, prefix, *, name, channel_index,  **kwargs):
        self.channel_index = channel_index
        super().__init__(prefix, name=name, **kwargs)


class Wave8(BaseInterface, Device):
    """
    Class for a wave8.

    Parameters
    ----------
    prefix : str
        Wave8 base PV.

    name : str
        Alias for the wave8.
    """

    tab_whitelist = ['isum', 'xpos', 'ypos']

    isum = Cpt(EpicsSignalRO, ':SUM', kind='normal')
    xpos = Cpt(EpicsSignalRO, ':XPOS', kind='normal')
    ypos = Cpt(EpicsSignalRO, ':YPOS', kind='normal')
    evr_channel = Cpt(Trigger, ':TRIG:TRIG0', kind='normal')
    do_config = Cpt(EpicsSignal, ':DO_CONFIG.PROC', kind='config')
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
        """Function to call the (pyQT) screen for a Wave8 box."""
        return ipm_screen('Wave8', self._prefix, self._prefix_ioc)

    def apply_configuration(self):
        """Put to the 'DO_CONFIG' PV, causing config PVs to be applied."""
        self.do_config.put(1)

    def configure(self):
        raise NotImplementedError


class IPM_Det(BaseInterface, Device):
    """Base class for IPM_IPIMB and IPM_Wave8. Not meant to be instantiated."""
    tab_component_names = True

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
        """Returns the detector's specified channel."""
        if (i >= self._num_channels or i < 0):
            raise ValueError("Invalid channel number!")
        else:
            return self.channels[i]

    @property
    def channels(self):
        """Returns a dictionary of all of the detector's channels."""
        return dict(self._channels)

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.det = getattr(self, self._det)
        self._channels = {i: getattr(self.det, 'ch%d' % i)
                          for i in range(self._num_channels)}


class IPM_IPIMB(IPMMotion, IPM_Det):
    """
%s

    has a `ipimb` component which represents the IPIMB box used for readout.
    """

    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    ipimb = FCpt(IPIMB, '{self.prefix_ipimb}', prefix_ioc='{self.prefix_ioc}')

    # IPIMB's have four channels
    _num_channels = 4
    _det = 'ipimb'

    def __init__(self, prefix, *, name, prefix_ipimb, prefix_ioc=None,
                 **kwargs):
        self.prefix_ipimb = prefix_ipimb
        self.prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)


class IPM_Wave8(IPMMotion, IPM_Det):
    """
%s

    has a `wave8` component which represents the Wave8 used for readout.
    """

    __doc__ = __doc__ % (IPM_base) + basic_positioner_init

    wave8 = FCpt(Wave8, '{self.prefix_wave8}', prefix_ioc='{self.prefix_ioc}')

    # Wave8's have sixteen channels
    _num_channels = 16
    _det = 'wave8'

    def __init__(self, prefix, *, name, prefix_wave8, prefix_ioc=None,
                 **kwargs):
        self.prefix_wave8 = prefix_wave8
        self.prefix_ioc = prefix_ioc
        super().__init__(prefix, name=name, **kwargs)
        self.det = self.wave8

    def configure(self):
        raise NotImplementedError


def IPM(prefix, *, name, **kwargs):
    """
    Factory function for an IPM.

    optional: IPIMB box or Wave8 for readout.

    Parameters
    ----------
    prefix : str
        Base PV for the IPM.

    name : str
        Alias for the IPM.

    prefix_ipimb : str, optional
        Base PV for IPIMB box.

    prefix_wave8 : str, optional
        BasePV for Wave8.
    """

    if 'prefix_ipimb' in kwargs:
        return IPM_IPIMB(prefix, name=name,
                         prefix_ipimb=kwargs.pop('prefix_ipimb'), **kwargs)
    elif 'prefix_wave8' in kwargs:
        return IPM_Wave8(prefix, name=name,
                         prefix_wave8=kwargs.pop('prefix_wave8'), **kwargs)
    else:
        return IPMMotion(prefix, name=name)
