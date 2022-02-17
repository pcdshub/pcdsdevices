import time

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from . import utils as key_press
from .device import GroupDevice
from .interface import BaseInterface


class Acromag(BaseInterface, GroupDevice):
    """
    Class for Acromag analog input/ouput signals.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the Acromag.

    name : str
        A name to refer to the Acromag.
    """

    # Components for each channel
    # Output channels
    ao1_0 = Cpt(EpicsSignal, ":ao1:0", kind='normal')
    ao1_1 = Cpt(EpicsSignal, ":ao1:1", kind='normal')
    ao1_2 = Cpt(EpicsSignal, ":ao1:2", kind='normal')
    ao1_3 = Cpt(EpicsSignal, ":ao1:3", kind='normal')
    ao1_4 = Cpt(EpicsSignal, ":ao1:4", kind='normal')
    ao1_5 = Cpt(EpicsSignal, ":ao1:5", kind='normal')
    ao1_6 = Cpt(EpicsSignal, ":ao1:6", kind='normal')
    ao1_7 = Cpt(EpicsSignal, ":ao1:7", kind='normal')
    ao1_8 = Cpt(EpicsSignal, ":ao1:8", kind='normal')
    ao1_9 = Cpt(EpicsSignal, ":ao1:9", kind='normal')
    ao1_10 = Cpt(EpicsSignal, ":ao1:10", kind='normal')
    ao1_11 = Cpt(EpicsSignal, ":ao1:11", kind='normal')
    ao1_12 = Cpt(EpicsSignal, ":ao1:12", kind='normal')
    ao1_13 = Cpt(EpicsSignal, ":ao1:13", kind='normal')
    ao1_14 = Cpt(EpicsSignal, ":ao1:14", kind='normal')
    ao1_15 = Cpt(EpicsSignal, ":ao1:15", kind='normal')

    # Input channels
    ai1_0 = Cpt(EpicsSignalRO, ":ai1:0", kind='normal')
    ai1_1 = Cpt(EpicsSignalRO, ":ai1:1", kind='normal')
    ai1_2 = Cpt(EpicsSignalRO, ":ai1:2", kind='normal')
    ai1_3 = Cpt(EpicsSignalRO, ":ai1:3", kind='normal')
    ai1_4 = Cpt(EpicsSignalRO, ":ai1:4", kind='normal')
    ai1_5 = Cpt(EpicsSignalRO, ":ai1:5", kind='normal')
    ai1_6 = Cpt(EpicsSignalRO, ":ai1:6", kind='normal')
    ai1_7 = Cpt(EpicsSignalRO, ":ai1:7", kind='normal')
    ai1_8 = Cpt(EpicsSignalRO, ":ai1:8", kind='normal')
    ai1_9 = Cpt(EpicsSignalRO, ":ai1:9", kind='normal')
    ai1_10 = Cpt(EpicsSignalRO, ":ai1:10", kind='normal')
    ai1_11 = Cpt(EpicsSignalRO, ":ai1:11", kind='normal')
    ai1_12 = Cpt(EpicsSignalRO, ":ai1:12", kind='normal')
    ai1_13 = Cpt(EpicsSignalRO, ":ai1:13", kind='normal')
    ai1_14 = Cpt(EpicsSignalRO, ":ai1:14", kind='normal')
    ai1_15 = Cpt(EpicsSignalRO, ":ai1:15", kind='normal')

    tab_component_names = True


def acromag_ch_factory_func(prefix, channel, *, signal_class=None, name=None,
                            **kwargs):
    """
    This is a factory function for creating an Acromag output or input signal.

    Parameters
    ----------
    prefix : str
        The base EPICS PV for the Acromag. E.g.: `XPP:USR:ai1`
    channel : int or str
        The channel number. E.g.: `1` [0-15]
    signal_class : str, optional
        Signal Class to use. E.g.: `EpicsSignalRO`, `EpicsSignal`. If `None`
        provided, it will use the prefix to try to generate the appropriate
        signal class.
    name : str, optional
        A name to refer to the Acromag Channel, if `None` it will use the
        prefix and channel to generate a name. E.g.: `ai_1` or `ao_1`.
    """
    if signal_class is None:
        signal_class = EpicsSignalRO if ':ai' in prefix else EpicsSignal
    name_prefix = 'ai_' if ':ai' in prefix else 'ao_'
    name = name or f'{name_prefix}{channel}'
    prefix = f'{prefix}:{channel}'
    return signal_class(prefix, name=name, kind='normal')


AcromagChannel = acromag_ch_factory_func


class Mesh(BaseInterface, Device):
    """
    Class for Mesh HV Supply that is connected to Acromag inputs and outputs.

    The standard Device ``name`` parameter is ignored here and replaced with
    ``"mesh_raw"``.

    Parameters
    ----------
    prefix : str
        Prefix of Acromag to be used.

    sp_ch : int
        Setpoint Acromag channel to which high voltage supply setpoint is
        connected. Range is 0 to 15.

    rb_ch : int
        Read back Acromag channel to which high voltage readback is connected.
        Range is 0 to 15.

    scale : float, optional
        Gain for high voltage supply to be controlled by the Acromag.
    """

    tab_whitelist = ['get_mesh_voltage', 'set_mesh_voltage',
                     'tweak_mesh_voltage']

    write_sig = FCpt(EpicsSignal, '{self.prefix}' + ':ao1:' + '{self.sp_ch}')
    read_sig = FCpt(EpicsSignalRO, '{self.prefix}' + ':ai1:' + '{self.rb_ch}')

    def __init__(self, prefix, sp_ch, rb_ch, scale=1000.0, name=None):
        self.scale = scale
        self.prefix = prefix
        self.sp_ch = sp_ch
        self.rb_ch = rb_ch
        super().__init__(prefix, name='mesh_raw')

    def get_raw_mesh_voltage(self):
        """
        Get the current acromag voltage that outputs to the HV supply, i.e.
        the voltage seen by the HV supply.
        """
        return self.read_sig.get()

    def get_mesh_voltage(self):
        """
        Get the current mesh voltage setpoint, i.e. the setpoint that the HV
        supply attempts to output.
        """
        return self.read_sig.get() * self.scale

    def set_mesh_voltage(self, hv_sp, wait=True):
        """
        Set mesh voltage to an absolute value in V.

        Parameters
        ----------
        hv_sp : float
            Desired power supply setpoint in V. Acromag will output
            necessary voltage such that the HV supply achieves the value
            passed to hv_sp.

        wait : bool, optional
            Indicates whether or not the program should pause when writing
            to a PV.

        do_print : bool, optional
            Indicates whether or not the program should print it's
            setpoint and readback values.
        """

        self.log.info('Setting mesh voltage...')
        hv_sp_raw = hv_sp / self.scale
        self.write_sig.put(hv_sp_raw)
        if wait:
            time.sleep(1.0)
        hv_rb_raw = self.read_sig.get()
        hv_rb = hv_rb_raw * self.scale
        self.log.info('Power supply setpoint: %s V' % hv_sp)
        self.log.info('Power supply readback: %s V' % hv_rb)

    def set_rel_mesh_voltage(self, delta_hv_sp, wait=True):
        """
        Increase/decrease the power supply setpoint by a specified amount.

        Parameters
        ----------
        delta_hv_sp : float
            Amount to increase/decrease the power supply setpoint (in V)
            from its current value. Use positive to increase and negative
            to decrease.
        """

        curr_hv_sp_raw = self.write_sig.get()
        curr_hv_sp = curr_hv_sp_raw * self.scale
        self.log.info('Previous power supply setpoint: %s V' % curr_hv_sp)
        new_hv_sp = curr_hv_sp + delta_hv_sp
        self.set_mesh_voltage(new_hv_sp, wait=wait)

    def tweak_mesh_voltage(self, delta_hv_sp, test_flag=False):
        """
        Increase/decrease power supply setpoint using the arrow keys.

        Use 'q' or ^C to exit tweak mode.

        Parameters
        ----------
        delta_hv_sp : float
            Amount to change voltage from its current value at each step,
            measured in volts. After calling with specified step size, use
            arrow keys to keep changing. Use absolute value of increment size.

        test_flag : bool, optional
            Flag used in testing functions to only run ``while True`` loop
            once - i.e. single tweak mode.
        """

        print('Use arrow keys (left, right) to step voltage (-, +)')
        while True:
            key = key_press.get_input()
            if key in ('q', None):
                return
            elif key == key_press.arrow_right:
                self.set_rel_mesh_voltage(delta_hv_sp, wait=False)
            elif key == key_press.arrow_left:
                self.set_rel_mesh_voltage(-delta_hv_sp, wait=False)
            if test_flag:
                return
