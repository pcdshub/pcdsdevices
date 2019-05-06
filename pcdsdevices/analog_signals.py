import time
import pcdsdevices.utils as key_press
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO


class Acromag(Device):
    """
    Class for Acromag analog input/ouput signals

    Parameters:
    -----------
    prefix : str
        The Epics base of the acromag

    name : str
        A name to prefer to the device
    """
    # Components for each channel
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

    def initialize_mesh(self, sp_ch, rb_ch, scale=1000.0):
        """
        Setup the Acromag for mesh power supply usage

        Parameters
        ----------
        sp_ch : int
            Setpoint Acromag channel to which high voltage supply setpoint
            is connected. Range is 0 to 15

        rb_ch : int
            Read back Acromag channel to which high voltage readback is
            connected. Range is 0 to 15

        scale : float, optional
            Gain for high voltage supply to be controlled by the Acromag
        """
        self.scale = scale
        self.rb_pv = getattr(self, 'ai1_%s' % rb_ch).pvname
        self.sp_pv = getattr(self, 'ao1_%s' % sp_ch).pvname
        self.mesh_raw = EpicsSignal(name='mesh_raw',
                                    read_pv=rb_pv,
                                    write_pv=sp_pv)

    def get_raw_mesh_voltage(self):
        """
        Get the current acromag voltage that outputs to the HV supply, i.e
        the voltage seen by the HV supply
        """
        # NOTE: For this to work, must use self.initialize_mesh first, may
        # want to make a check for this, otherwise will get error
        return self.mesh_raw.get()

    def get_mesh_voltage(self):
        """
        Get the current mesh voltage setpoint, i.e the setpoint that the HV
        supply attempts to output
        """
        return self.mesh_raw.get() * self.scale

    def set_mesh_voltage(self, hv_sp, wait=True, do_print=True):
        """
        Set mesh voltage to an absolute value in V

        Parameters
        ----------
        hv_sp : float
            Desired power supply setpoint in V. Acromag will output
            necessary voltage such that the HV supply achieves the value
            passed to hv_sp

        wait : bool, optional
            Indicates whether or not the program should pause when writing
            to a PV

        do_print : bool, optional
            Indicates whether or not the program should print it's
            setpoint and readback values
        """
        if do_print:
            print('Setting mesh voltage...')
        hv_sp_raw = hv_sp / self.scale
        self.mesh_raw.put(hv_sp_raw)
        if wait:
            time.sleep(1.0)
        hv_rb_raw = self.mesh_raw.get()
        hv_rb = hv_rb_raw * self.scale
        if do_print:
            print('Power supply setpoint: %s V' % hv_sp)
            print('Power supply readback: %s V' % hv_rb)

    def set_rel_mesh_voltage(self, delta_hv_sp, wait=True, do_print=True):
        """
        Increase/decrease the power supply setpoint by a specified amount

        Parameters
        ----------
        delta_hv_sp : float
            Amount to increase/decrease the power supply setpoint (in V)
            from its current value. Use positive to increase and negative
            to decrease
        """
        curr_hv_sp_raw = self.mesh_raw.get_setpoint()
        curr_hv_sp = curr_hv_sp_raw * self.scale
        if do_print:
            print('Setting voltage...')
            print('Previous power supply setpoint: %s V' % curr_hv_sp)
        new_hv_sp = curr_hv_sp * self.scale
        self.set_mesh_voltage(new_hv_sp, wait=wait, do_print=do_print)

    def tweak_mesh_voltage(self, delta_hv_sp):
        """
        Increase/decrease power supply setpoint by specified amount using
        the arrow keys

        Parameters
        ----------
        delta_hv_sp : float (V)
            Amount to change voltage from its current value at each step.
            After calling with specified step size, use arrow keys to keep
            changing. Use absolute value of increment size.
        ^C :
            exits tweak mode
        """
        print('Use arrow keys (left, right) to step voltage (-, +)')
        while True:
            key = key_press.get_input()
            if key in ('q', None):
                return
            elif key == key_press.arrow_right:
                self.set_rel_mesh_voltage(delta_hv_sp, wait=False,
                                          do_print=False)
            elif key == key_press.arrow_left:
                self.set_rel_mesh_voltage(-delta_hv_sp, wait=False,
                                          do_print=False)
