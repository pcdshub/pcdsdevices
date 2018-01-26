import logging
import time

from ophyd.device import Component as Cmp
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .inout import InOutPositioner
from .mv_interface import FltMvInterface

logger = logging.getLogger(__name__)
MAX_FILTERS = 12


class Filter(InOutPositioner):
    """
    A single attenuation blade.
    """
    state = Cmp(EpicsSignal, ':STATE', write_pv=':GO')
    thickness = Cmp(EpicsSignal, ':THICK')
    material = Cmp(EpicsSignal, ':MATERIAL')
    stuck = Cmp(EpicsSignal, ':STUCK')


class AttBase(PVPositioner, FltMvInterface):
    """
    Base class for the attenuators. Does not include filters, because the
    number of filters can vary.
    """
    # Positioner Signals
    setpoint = Cmp(EpicsSignal, ':COM:R_DES')
    readback = Cmp(EpicsSignalRO, ':COM:R_CUR')
    actuate = Cmp(EpicsSignal, ':COM:GO')
    done = Cmp(EpicsSignalRO, ':COM:STATUS')

    # Attenuator Signals
    energy = Cmp(EpicsSignalRO, ':COM:T_CALC.VALE')
    trans_ceil = Cmp(EpicsSignalRO, ':COM:R_CEIL')
    trans_floor = Cmp(EpicsSignalRO, ':COM:R_FLOOR')
    user_energy = Cmp(EpicsSignal, ':COM:EDES')
    eget_cmd = Cmp(EpicsSignal, ':COM:EACT.SCAN')

    # Aux Signals
    calcpend = Cmp(EpicsSignalRO, ':COM:CALCP')

    egu = ''  # Transmission is a unitless ratio
    done_value = 0
    _default_read_attrs = ['readback']

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, limits=(0, 1), **kwargs)
        self.filters = []
        for i in range(1, MAX_FILTERS + 1):
            try:
                self.filters.append(getattr(self, 'filter{}'.format(i)))
            except AttributeError:
                break

    @property
    def actuate_value(self):
        """
        Sets the value we use in the GO command. This command will return 2 if
        the setpoint is closer to the ceiling than the floor, or 3 otherwise.
        In the unlikely event of a tie, we choose the floor.

        This will wait until a pending calculation completes before returning.
        """
        timeout = 1
        start = time.time()
        while self.calcpend.get() != 0:
            if time.time() - start > timeout:
                break
            time.sleep(0.01)

        goal = self.setpoint.get()
        ceil = self.trans_ceil.get()
        floor = self.trans_floor.get()
        if abs(goal - ceil) < abs(goal - floor):
            return 2
        else:
            return 3

    def set_energy(self, energy=None):
        """
        Sets the energy to use for transmission calculations.

        Parameters
        ----------
        energy: number, optional
            If provided, this is the energy we'll use for the transmission
            calcluations. If omitted, we'll clear any set energy and use the
            current beam energy instead.
        """
        if energy is None:
            logger.debug('Setting %s to use live energy', self.name or self)
            self.eget_cmd.put(6)
        else:
            logger.debug('Setting %s to use energy=%s',
                         self.name, energy)
            self.eget_cmd.put(0, use_complete=True)
            self.user_energy.put(energy)

    @property
    def transmission(self):
        """
        Ratio of pass-through beam to incoming beam. This is a value between
        1 (full beam) and 0 (no beam).
        """
        return self.position

    @property
    def inserted(self):
        """
        True if any blade is inserted
        """
        return self.position < 1

    @property
    def removed(self):
        """
        True if all blades are removed
        """
        return self.position == 1

    def insert(self, wait=False, timeout=None, moved_cb=None):
        """
        Block the beam
        """
        return self.move(0, wait=wait, timeout=timeout, moved_cb=moved_cb)

    def remove(self, wait=False, timeout=None, moved_cb=None):
        """
        Bring the attenuator fully out of the beam
        """
        return self.move(1, wait=wait, timeout=timeout, moved_cb=moved_cb)

    def stage(self):
        """
        Store the original positions of all filter blades.
        This is better then storing and restoring the transmission because the
        mechanical state associated with a particular transmission changes with
        the beam energy.
        """
        for filt in self.filters:
            # If state is invalid, try to remove at end
            if filt.position in filt._invalid_states:
                self._original_vals[filt.state] = filt.out_states[0]
            # Otherwise, remember so we can restore
            else:
                self._original_vals[filt.state] = filt.state.value
        return super().stage()


class AttBase3rd(AttBase):
    """
    Attenuator class to use the 3rd harmonic values instead of the fundamental
    values.
    """
    # Positioner Signals
    setpoint = Cmp(EpicsSignal, ':COM:R3_DES')
    readback = Cmp(EpicsSignalRO, ':COM:R3_CUR')

    # Attenuator Signals
    energy = Cmp(EpicsSignalRO, ':COM:T_CALC.VALH')
    trans_ceil = Cmp(EpicsSignalRO, ':COM:R3_CEIL')
    trans_floor = Cmp(EpicsSignalRO, ':COM:R3_FLOOR')
    user_energy = Cmp(EpicsSignal, ':COM:E3DES')


def _make_att_classes(max_filters, base, name):
    att_classes = {}
    for i in range(1, max_filters + 1):
        att_filters = {}
        for n in range(1, i + 1):
            comp = Cmp(Filter, ':{:02}'.format(n))
            att_filters['filter{}'.format(n)] = comp

        name = '{}{}'.format(name, i)
        cls = type(name, (base,), att_filters)
        # Store the number of filters
        cls.num_att = i
        att_classes[i] = cls
    return att_classes


_att_classes = _make_att_classes(MAX_FILTERS, AttBase, 'Attenuator')
_att3_classes = _make_att_classes(MAX_FILTERS, AttBase3rd, 'Attenuator3rd')


def Attenuator(prefix, n_filters, *, name, use_3rd=False, **kwargs):
    """
    Factory function for instantiating an attenuator with the correct filter
    components given the number required.
    """
    if use_3rd:
        cls = _att3_classes[n_filters]
    else:
        cls = _att_classes[n_filters]
    return cls(prefix, name=name, **kwargs)
