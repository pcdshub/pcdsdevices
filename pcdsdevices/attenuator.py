"""
Module for `Attenuator` and related classes.
"""
import logging
import time

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import Signal, EpicsSignal, EpicsSignalRO

from .inout import InOutPositioner
from .interface import FltMvInterface

logger = logging.getLogger(__name__)
MAX_FILTERS = 12


class Filter(InOutPositioner):
    """
    A single attenuation blade.

    Each of these has it's own in/out state, thickness, and material that are
    used in the attenuator IOC's calculations. It also has the capability to
    mark itself as ``STUCK IN`` or ``STUCK OUT`` so the transmission calculator
    can work around mechanical problems.

    This is not intended to be instantiated by a user, but instead included as
    a ``Component`` in a subclass of `AttBase`. You can instantiate these
    classes via the `Attenuator` factory function.
    """
    state = Cpt(EpicsSignal, ':STATE', write_pv=':GO', kind='hinted')
    thickness = Cpt(EpicsSignal, ':THICK', kind='config')
    material = Cpt(EpicsSignal, ':MATERIAL', kind='config')
    stuck = Cpt(EpicsSignal, ':IS_STUCK', kind='omitted')

    tab_component_names = True


class FeeFilter(InOutPositioner):
    """
    A single attenuation blade, as implemented in the FEE
    """
    state = Cpt(EpicsSignal, ':STATE', write_pv=':CMD')

    states_list = ['IN', 'OUT', 'FAIL']
    _invalid_states = ['FAIL']
    _unknown = 'XSTN'


class AttBase(FltMvInterface, PVPositioner):
    """
    Base class for the attenuators.

    This is a device that puts an array of filters in or out to achieve a
    desired transmission ratio.

    This class does not include filters, because the number of filters can
    vary. You should not instantiate this class directly, but instead use the
    `Attenuator` factory function.
    """
    # Positioner Signals
    setpoint = Cpt(EpicsSignal, ':COM:R_DES', kind='normal')
    readback = Cpt(EpicsSignalRO, ':COM:R_CUR', kind='hinted')
    actuate = Cpt(EpicsSignal, ':COM:GO', kind='omitted')
    done = Cpt(EpicsSignalRO, ':COM:STATUS', kind='omitted')

    # Attenuator Signals
    energy = Cpt(EpicsSignalRO, ':COM:T_CALC.VALE', kind='normal')
    trans_ceil = Cpt(EpicsSignalRO, ':COM:R_CEIL', kind='omitted')
    trans_floor = Cpt(EpicsSignalRO, ':COM:R_FLOOR', kind='omitted')
    user_energy = Cpt(EpicsSignal, ':COM:EDES', kind='omitted')
    eget_cmd = Cpt(EpicsSignal, ':COM:EACT.SCAN', kind='omitted')

    # Aux Signals
    calcpend = Cpt(EpicsSignalRO, ':COM:CALCP', kind='omitted')

    egu = ''  # Transmission is a unitless ratio
    done_value = 0

    # QIcon for UX
    _icon = 'fa.barcode'
    # Subscription Types
    SUB_STATE = 'state'
    # Tab complete whitelist
    tab_whitelist = ['set_energy']

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, limits=(0, 1), **kwargs)
        self.filters = []
        self._has_subscribed_state = False
        for i in range(1, MAX_FILTERS + 1):
            try:
                self.filters.append(getattr(self, 'filter{}'.format(i)))
            except AttributeError:
                break

    @property
    def actuate_value(self):
        """
        Sets the value we use in the GO command. This command will return 3 if
        the setpoint is closer to the ceiling than the floor, or 2 otherwise.
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

        if abs(goal - ceil) > abs(goal - floor):
            return 2
        else:
            return 3

    def set_energy(self, energy=None):
        """
        Sets the energy to use for transmission calculations.

        Parameters
        ----------
        energy: ``number``, optional
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
        ``True`` if any blade is inserted
        """
        return self.position < 1

    @property
    def removed(self):
        """
        ``True`` if all blades are removed
        """
        return self.position == 1

    def insert(self, wait=False, timeout=None, moved_cb=None):
        """
        Block the beam by setting transmission to zero
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

        This is a ``bluesky`` method called to set up the device for a scan.
        At the end of the scan, ``unstage`` should be called to restore the
        original positions of the filter blades.

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

    def _setup_move(self, position):
        """
        If we're at a destination, short-circuit the done.

        This was needed because the status pv in the attenuator IOC does not
        react if we request a move to a transmission we've already reached.
        Therefore, this prevents a pointless timeout.
        """
        old_position = self.position
        super()._setup_move(position)
        ceil = self.trans_ceil.get()
        floor = self.trans_floor.get()
        if any(np.isclose((old_position, old_position), (ceil, floor))):
            moving_val = 1 - self.done_value
            self._move_changed(value=moving_val)
            self._move_changed(value=self.done_value)

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if event_type is None:
            event_type = self._default_sub
        if event_type == self.SUB_STATE and not self._has_subscribed_state:
            self.done.subscribe(self._run_filt_state, run=False)
            self._has_subscribed_state = True
        return cid

    def _run_filt_state(self, *args, **kwargs):
        kwargs.pop('sub_type')
        kwargs.pop('obj')
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)


class AttBase3rd(AttBase):
    """
    `Attenuator` class to use the 3rd harmonic values.

    This is exactly the same as the normal `AttBase`, but with the alternative
    transmission PVs. It can be instantiated using the ``use_3rd`` argument in
    the `Attenuator` factory function.
    """
    # Positioner Signals
    setpoint = Cpt(EpicsSignal, ':COM:R3_DES', kind='normal')
    readback = Cpt(EpicsSignalRO, ':COM:R3_CUR', kind='hinted')

    # Attenuator Signals
    energy = Cpt(EpicsSignalRO, ':COM:T_CALC.VALH', kind='normal')
    trans_ceil = Cpt(EpicsSignalRO, ':COM:R3_CEIL', kind='omitted')
    trans_floor = Cpt(EpicsSignalRO, ':COM:R3_FLOOR', kind='omitted')
    user_energy = Cpt(EpicsSignal, ':COM:E3DES', kind='omitted')


class FeeAtt(AttBase):
    """
    Old attenuator IOC in the FEE.
    """
    # Positioner Signals
    setpoint = Cpt(EpicsSignal, ':RDES', kind='normal')
    readback = Cpt(EpicsSignal, ':RACT', kind='hinted')
    actuate = Cpt(EpicsSignal, ':GO', kind='omitted')
    done = None

    # Attenuator Signals
    energy = Cpt(EpicsSignalRO, ':ETOA.E', kind='normal')
    trans_ceil = Cpt(EpicsSignalRO, ':R_CEIL', kind='omitted')
    trans_floor = Cpt(EpicsSignalRO, ':R_FLOOR', kind='omitted')
    user_energy = Cpt(EpicsSignal, ':EDES', kind='omitted')
    eget_cmd = Cpt(EpicsSignal, ':EACT.SCAN', kind='omitted')

#   status = None
    calcpend = Cpt(Signal, value=0)

    # Hardcode filters for FEE, because there is only one.
    filter1 = FCpt(FeeFilter, '{self._filter_prefix}1')
    filter2 = FCpt(FeeFilter, '{self._filter_prefix}2')
    filter3 = FCpt(FeeFilter, '{self._filter_prefix}3')
    filter4 = FCpt(FeeFilter, '{self._filter_prefix}4')
    filter5 = FCpt(FeeFilter, '{self._filter_prefix}5')
    filter6 = FCpt(FeeFilter, '{self._filter_prefix}6')
    filter7 = FCpt(FeeFilter, '{self._filter_prefix}7')
    filter8 = FCpt(FeeFilter, '{self._filter_prefix}8')
    filter9 = FCpt(FeeFilter, '{self._filter_prefix}9')
    num_att = 9

    def __init__(self, prefix='SATT:FEE1:320', *, name='FeeAtt', **kwargs):
        self._filter_prefix = prefix[:-1]
        super().__init__(prefix, name=name, **kwargs)


def _make_att_classes(max_filters, base, name):
    """
    Generate all possible subclasses.
    """
    att_classes = {}
    for i in range(1, max_filters + 1):
        att_filters = {}
        for n in range(1, i + 1):
            comp = Cpt(Filter, ':{:02}'.format(n))
            att_filters['filter{}'.format(n)] = comp

        cls_name = '{}{}'.format(name, i)
        cls = type(cls_name, (base,), att_filters)
        # Store the number of filters
        cls.num_att = i
        att_classes[i] = cls
    return att_classes


_att_classes = _make_att_classes(MAX_FILTERS, AttBase, 'Attenuator')
_att3_classes = _make_att_classes(MAX_FILTERS, AttBase3rd, 'Attenuator3rd')


def Attenuator(prefix, n_filters, *, name, use_3rd=False, **kwargs):
    """
    A series of filters that attenuates the beam.

    This is a factory function for instantiating a subclass of `AttBase` or
    `AttBase3rd` with the correct number of `Filter` components.

    The `Filter` components will be named ``filter1``, ``filter2``, ...
    ``filter10``, ...

    Parameters
    ----------
    prefix: ``str``
        The EPICS prefix that identifies the attenuator, e.g. ``XPP:ATT``

    n_filters: ``int``
        The number of filters in the attenuator.

    name: ``str``
        An identifying name for the attenuator.

    use_3rd: ``bool``, optional
        If ``True``, we'll use the third harmonic transmissions instead of the
        fundamntal frequency.
    """
    if use_3rd:
        cls = _att3_classes[n_filters]
    else:
        cls = _att_classes[n_filters]
    return cls(prefix, name=name, **kwargs)


'''
# WIP
def set_combined_attenuation(attenuation, *attenuators):
    for i in range(len(attenuators)):
        if i < len(attenuators)-1:
            attenuators[i].actuate_value(force_ceil=True)
        else:
            attenuators[i].actuate_value()
'''
