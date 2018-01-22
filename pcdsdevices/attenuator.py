import logging
import time

from ophyd.device import Component as Cmp, FormattedComponent as FCmp
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import DerivedSignal, EpicsSignal, EpicsSignalRO

from .inout import InOutPositioner

logger = logging.getLogger(__name__)
MAX_FILTERS = 12


class Filter(InOutPositioner):
    """
    A single attenuation blade, as implemented in the hard xray hutches.
    """
    state = Cmp(EpicsSignal, ':STATE', write_pv=':GO')
    thickness = Cmp(EpicsSignal, ':THICK')
    material = Cmp(EpicsSignal, ':MATERIAL')
    stuck = Cmp(EpicsSignal, ':STUCK')


class AttDoneSignal(DerivedSignal):
    """
    Signal that is 1 when all filters are done moving and 0 otherwise. This is
    derived from the STATUS PV, which can be OK, MOVING, FAULTED (0, 1, 2)
    """
    pass


class AttBase(PVPositioner):
    """
    Base class for the attenuators. Does not include filters, because the
    number of filters can vary.
    """
    # Positioner Signals
    setpoint = Cmp(EpicsSignal, ':R_DES')
    readback = Cmp(EpicsSignalRO, ':R_CUR')
    actuate = Cmp(EpicsSignal, ':GO')
    done = Cmp(AttDoneSignal)

    # Attenuator Signals
    energy = Cmp(EpicsSignalRO, ':T_CALC.VALE')
    trans_ceil = Cmp(EpicsSignalRO, ':R_CEIL')
    trans_floor = Cmp(EpicsSignalRO, ':R_FLOOR')
    user_energy = Cmp(EpicsSignal, ':EDES')
    eget_cmd = Cmp(EpicsSignal, ':EACT.SCAN')

    # Aux Signals
    status = Cmp(EpicsSignalRO, ':STATUS')
    calcpend = Cmp(EpicsSignalRO, ':CALCP')

    egu = ''  # Transmission is a unitless ratio
    _default_read_attrs = ['readback']

    def __init__(self, prefix, *, name, **kwargs):
        self._filters = []
        super().__init__(prefix, name=name, limits=(0, 1), **kwargs)

    @property
    def filters(self):
        """
        List of filters that are part of this att.
        """
        if not self._filters:
            for i in range(1, MAX_FILTERS + 1):
                try:
                    self._filters.append(getattr(self, 'filter{}'.format(i)))
                except AttributeError:
                    break
        return self._filters

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

    def insert(self):
        """
        Block the beam
        """
        return self.move(0)

    def remove(self):
        """
        Bring the attenuator fully out of the beam
        """
        return self.move(1)

    def stage(self):
        """
        Store the original positions of all filter blades
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


def _make_att_classes(max_filters):
    att_classes = {}
    for i in range(1, max_filters + 1):
        att_filters = {}
        for n in range(1, i + 1):
            num = ':{:02}'.format(n)
            comp = FCmp(Filter, '{self._filter_prefix}' + num)
            att_filters['filter{}'.format(n)] = comp

        name = 'Attenuator{}'.format(i)
        cls = type(name, (AttBase,), att_filters)
        # Store the number of filters
        cls.num_att = i
        att_classes[i] = cls
    return att_classes


_att_classes = _make_att_classes(MAX_FILTERS)


def Attenuator(prefix, n_filters, *, name, **kwargs):
    """
    Factory function for instantiating an attenuator with the correct filter
    components given the number required.
    """
    return _att_classes[n_filters](prefix, name=name, **kwargs)
