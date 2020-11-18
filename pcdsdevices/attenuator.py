"""
Module for `Attenuator` and related classes.
"""
import enum
import logging
import time

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import DynamicDeviceComponent as DDC
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositioner, PVPositionerPC
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal, SignalRO

from .component import UnrelatedComponent as UCpt
from .epics_motor import BeckhoffAxis
from .inout import InOutPositioner, TwinCATInOutPositioner
from .interface import BaseInterface, FltMvInterface, LightpathInOutMixin
from .signal import InternalSignal
from .variety import set_metadata
from .utils import get_status_value

logger = logging.getLogger(__name__)
MAX_FILTERS = 12


class Filter(InOutPositioner):
    """
    A single attenuation blade.

    Each of these has it's own in/out state, thickness, and material that are
    used in the attenuator IOC's calculations. It also has the capability to
    mark itself as 'STUCK IN' or 'STUCK OUT' so the transmission calculator
    can work around mechanical problems.

    This is not intended to be instantiated by a user, but instead included as
    a :class:`~ophyd.device.Component` in a subclass of :class:`AttBase`. You
    can instantiate these classes via the :func:`Attenuator` factory function.
    """

    status = Cpt(InternalSignal, kind='normal')
    state = Cpt(EpicsSignal, ':STATE', write_pv=':GO', kind='normal')
    stuck = Cpt(EpicsSignal, ':IS_STUCK', kind='normal')
    thickness = Cpt(EpicsSignal, ':THICK', kind='config')
    material = Cpt(EpicsSignal, ':MATERIAL', kind='config')

    tab_component_names = True

    def __init__(self, prefix, *, name, **kwargs):
        self._status_state = None
        self._stuck_state = None
        super().__init__(prefix, name=name, **kwargs)

    @state.sub_value
    def _state_update(self, *args, value, **kwargs):
        self._status_state = value
        self._status_update()

    @stuck.sub_value
    def _stuck_update(self, *args, value, **kwargs):
        self._stuck_state = value
        self._status_update()

    def _status_update(self):
        if self._stuck_state == 1:
            self.status.put(BladeStateEnum.STUCK_IN, force=True)
        elif self._stuck_state == 2:
            self.status.put(BladeStateEnum.STUCK_OUT, force=True)
        elif self._status_state == 1:
            self.status.put(BladeStateEnum.IN, force=True)
        elif self._status_state == 2:
            self.status.put(BladeStateEnum.OUT, force=True)
        else:
            self.status.put(BladeStateEnum.Unknown, force=True)


class FeeFilter(InOutPositioner):
    """A single attenuation blade, as implemented in the FEE."""

    status = Cpt(InternalSignal, kind='normal')
    state = Cpt(EpicsSignal, ':STATE', write_pv=':CMD')

    states_list = ['IN', 'OUT', 'FAIL']
    _invalid_states = ['FAIL']
    _unknown = 'XSTN'

    @state.sub_value
    def _status_update(self, *args, value, **kwargs):
        if value == 1:
            self.status.put(BladeStateEnum.IN, force=True)
        elif value == 2:
            self.status.put(BladeStateEnum.OUT, force=True)
        else:
            self.status.put(BladeStateEnum.Unknown, force=True)


class AttBase(FltMvInterface, PVPositioner):
    """
    Base class for attenuators with fundamental frequency.

    This is a device that puts an array of filters in or out to achieve a
    desired transmission ratio.

    This class does not include filters, because the number of filters can
    vary. You should not instantiate this class directly, but instead use the
    :func:`Attenuator` factory function.
    """
    # fundamental frequency components
    # Positioner Signals
    setpoint = Cpt(EpicsSignal, ':COM:R_DES', auto_monitor=True,
                   kind='normal')
    readback = Cpt(EpicsSignalRO, ':COM:R_CUR', auto_monitor=True,
                   kind='hinted')
    actuate = Cpt(EpicsSignal, ':COM:GO', kind='omitted')
    done = Cpt(EpicsSignalRO, ':COM:STATUS', auto_monitor=True,
               kind='omitted')

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
        Sets the value we use in the 'GO' command.

        This command will return 3 if the setpoint is closer to the ceiling
        than the floor, or 2 otherwise. In the unlikely event of a tie, we
        choose the floor.

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
        energy : number, optional
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
        Ratio of pass-through beam to incoming beam as a value between
        1 (full beam) and 0 (no beam).
        """
        return self.position

    @property
    def inserted(self):
        """`True` if any blade is inserted."""
        return self.position < 1

    @property
    def removed(self):
        """`True` if all blades are removed."""
        return self.position == 1

    def insert(self, wait=False, timeout=None, moved_cb=None):
        """Block the beam by setting transmission to zero."""
        return self.move(0, wait=wait, timeout=timeout, moved_cb=moved_cb)

    def remove(self, wait=False, timeout=None, moved_cb=None):
        """Bring the attenuator fully out of the beam."""
        return self.move(1, wait=wait, timeout=timeout, moved_cb=moved_cb)

    def stage(self):
        """
        Store the original positions of all filter blades.

        This is a ``bluesky`` method called to set up the device for a scan.
        At the end of the scan, :meth:`.unstage` should be called to restore
        the original positions of the filter blades.

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
                self._original_vals[filt.state] = filt.state.get()
        return super().stage()

    def _setup_move(self, position):
        """
        If we're at a destination, short-circuit the done.

        This was needed because the status PV in the attenuator IOC does not
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
            if self.done is not None:
                obj = self.done
            else:
                obj = self.readback
            obj.subscribe(self._run_filt_state, run=False)
            self._has_subscribed_state = True
        return cid

    def _run_filt_state(self, *args, **kwargs):
        kwargs.pop('sub_type')
        kwargs.pop('obj')
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)

    def format_status_info(self, status_info):
        """
        Override status info handler to render the att

        Display attenuator status info in the ipython terminal.

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
        # Get the attenuator statuses
        blade_states = []
        for i in range(1, MAX_FILTERS + 1):
            try:
                filter_info = status_info[f'filter{i}']
            except KeyError:
                break
            status = get_status_value(filter_info, 'status', 'value')
            blade_states.append(status)

        states = '\n'.join(render_ascii_att(blade_states))

        energy = get_status_value(status_info, 'energy', 'value') * 1e3
        energy_3rd = get_status_value(status_info, 'energy_3rd', 'value')
        trans = get_status_value(status_info, 'position')

        if energy_3rd != 'N/A':
            energy_3rd = energy_3rd * 1e3
            return f"""\
{states}
Transmission for 1st harmonic (E={energy:.3} keV): {trans:.4E}
Transmission for 3rd harmonic (E={energy_3rd:.3} keV): {trans:.4E}
"""
        else:
            return f"""\
{states}
Transmission for 1st harmonic (E={energy:.3} keV): {trans:.4E}
"""


class AttBaseWith3rdHarmonic(AttBase):
    """
    Base class for attenuators with 3rd harmonic frequency.

    This base class contains 3rd harmonic frequncy components.
    You should not instantiate this class directly, but instead use the
    :func:`Attenuator` factory function.
    """
    # Positioner Signals
    setpoint_3rd = Cpt(EpicsSignal, ':COM:R3_DES', kind='normal')
    readback_3rd = Cpt(EpicsSignalRO, ':COM:R3_CUR', kind='hinted')

    # Attenuator Signals
    energy_3rd = Cpt(EpicsSignalRO, ':COM:T_CALC.VALH', kind='normal')
    trans_ceil_3rd = Cpt(EpicsSignalRO, ':COM:R3_CEIL', kind='omitted')
    trans_floor_3rd = Cpt(EpicsSignalRO, ':COM:R3_FLOOR', kind='omitted')
    user_energy_3rd = Cpt(EpicsSignal, ':COM:E3DES', kind='omitted')


class FeeAtt(AttBase, PVPositionerPC):
    """Old attenuator IOC in the FEE."""
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

    # status = None
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


def _make_att_classes(max_filters, base_with_3rd_harmonic, name):
    """Generate all possible subclasses."""
    att_classes = {}
    for i in range(1, max_filters + 1):
        att_filters = {}
        for n in range(1, i + 1):
            comp = Cpt(Filter, ':{:02}'.format(n))
            att_filters['filter{}'.format(n)] = comp

        cls_name = '{}{}'.format(name, i)
        cls = type(cls_name, (base_with_3rd_harmonic,), att_filters)
        cls.num_att = i
        att_classes[i] = cls
    return att_classes


_att_classes = _make_att_classes(
    MAX_FILTERS, AttBaseWith3rdHarmonic, 'Attenuator')


def Attenuator(prefix, n_filters, *, name, **kwargs):
    """
    A series of filters that attenuates the beam.

    This is a factory function for instantiating a subclass of :class:`AttBase`
    with the correct number of :class:`Filter` components.

    The :class:`Filter` components will be named 'filter1', 'filter2', ...
    'filter10', ...

    Parameters
    ----------
    prefix : str
        The EPICS prefix that identifies the attenuator, e.g. 'XPP:ATT'

    n_filters : int
        The number of filters in the attenuator.

    name : str
        An identifying name for the attenuator.
    """
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


class FEESolidAttenuatorBlade(BaseInterface, Device, LightpathInOutMixin):
    lightpath_cpts = ['state']

    state = Cpt(TwinCATInOutPositioner, ':STATE')
    motor = Cpt(BeckhoffAxis, '')


class GasAttenuator(BaseInterface, Device):
    """
    AT*:GAS, Base class for an LCLS-II XTES gas attenuator.

    Parameters
    ----------
    prefix : str
        Full Gas Attenuator base PV.

    name : str
        Alias for the Gas Attenuator.

    Notes
    -----
    The HXR gas attenuator was not recommissioned so this class alone
    represents the gas attenuators present at this time.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')


class AttenuatorCalculatorFilter(BaseInterface, Device):
    material = Cpt(
        EpicsSignal, 'Material', kind='hinted', string=True,
        doc='The material formula (e.g., Si, C)'
    )
    thickness = Cpt(
        EpicsSignal, 'Thickness', kind='hinted',
        doc='Thickness in micron',
    )
    is_stuck = Cpt(
        EpicsSignal, 'IsStuck', kind='hinted',
        doc='Is the filter stuck / unusable?',
    )
    closest_energy = Cpt(
        EpicsSignalRO, 'ClosestEnergy_RBV', kind='config',
        doc='Closest tabulated energy available to the requested one',
    )
    transmission = Cpt(EpicsSignalRO, 'Transmission_RBV', kind='normal',
                       doc='Normalized transmission at the reported energy',
                       )
    set_metadata(transmission, dict(variety='scalar',
                                    display_format='exponential'))

    transmission_3omega = Cpt(
        EpicsSignalRO, 'Transmission3Omega_RBV', kind='normal',
        doc='Normalized transmission at 3 * the reported energy',
                              )
    set_metadata(transmission_3omega, dict(variety='scalar',
                                           display_format='exponential'))

    def __init__(self, *args, index, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index


class AttenuatorCalculatorBase(BaseInterface, Device):
    """Base class for new-style caproto IOC attenuator calculator devices."""

    # QIcon for UX
    _icon = 'fa.barcode'

    calc_mode = Cpt(
        EpicsSignal, ':SYS:CalcMode', kind='config', string=True,
        doc='Floor or Ceiling calculation',
    )

    energy_source = Cpt(
        EpicsSignal, ':SYS:EnergySource', kind='config', string=True,
        doc='Use beamline photon energy or custom energy?',
    )

    energy_custom = Cpt(
        EpicsSignal, ':SYS:CustomPhotonEnergy', kind='config',
        doc='Custom energy to use for calculations [eV]',
    )

    energy_actual = Cpt(
        EpicsSignalRO, ':SYS:ActualPhotonEnergy_RBV', kind='normal',
        doc='The reported beamline photon energy [eV]',
    )

    actual_transmission = Cpt(
        EpicsSignalRO, ':SYS:ActualTransmission_RBV', kind='normal',
        doc='Actual normalized transmission value',
    )
    set_metadata(actual_transmission,
                 dict(variety='scalar', display_format='exponential'))

    actual_transmission_3omega = Cpt(
        EpicsSignalRO, ':SYS:Actual3OmegaTransmission_RBV', kind='normal',
        doc='Actual 3 omega normalized transmission value',
    )
    set_metadata(actual_transmission_3omega,
                 dict(variety='scalar', display_format='exponential'))

    desired_transmission = Cpt(
        EpicsSignal, ':SYS:DesiredTransmission', kind='normal',
        doc='Desired normalized transmission value',
    )
    set_metadata(desired_transmission, dict(variety='scalar',
                                            display_format='exponential'))

    last_energy = Cpt(
        EpicsSignalRO, ':SYS:LastPhotonEnergy_RBV', kind='config',
        doc=('The photon energy used for the previous calculation; i.e., '
             'the one that goes along with `best_config`.'),
    )

    # NOTE: this variant exists as well but duplicates the bitmask information:
    # best_config = Cpt(
    #     EpicsSignalRO, ':SYS:BestConfiguration_RBV', kind='normal',
    #     doc='The best configuration of filters for the desired transmission',
    # )
    # set_metadata(best_config, dict(variety='array-nd'))
    # # TODO: array-tabular would be nice, but does not work in typhos yet

    best_config_bitmask = Cpt(
        EpicsSignalRO, ':SYS:BestConfigurationBitmask_RBV', kind='normal',
        doc='The best configuration of filters for the desired transmission.',
    )
    set_metadata(best_config_bitmask, dict(variety='bitmask', bits=18))
    # TODO: array-tabular would be nice, but does not work in typhos yet

    best_config_error = Cpt(
        EpicsSignalRO, ':SYS:BestConfigError_RBV', kind='normal',
        doc='Desired to calculated transmission error',
    )

    # NOTE: this variant exists as well but duplicates the bitmask information:
    # active_config = Cpt(
    #     EpicsSignalRO, ':SYS:ActiveConfiguration_RBV', kind='omitted',
    #     doc='Where the filters are now',
    # )
    # set_metadata(active_config, dict(variety='array-nd'))
    # TODO: array-tabular would be nice, but does not work in typhos yet

    active_config_bitmask = Cpt(
        EpicsSignalRO, ':SYS:ActiveConfigurationBitmask_RBV', kind='normal',
        doc='Where the filters are now (as an integer)',
    )
    set_metadata(active_config_bitmask, dict(variety='bitmask', bits=18))

    # NOTE: this variant exists as well but duplicates the bitmask information:
    # filters_moving = Cpt(
    #     EpicsSignalRO, ':SYS:FiltersMoving_RBV', kind='normal',
    #     doc='Filter-by-filter motion status (1 if moving)',
    # )
    # set_metadata(filters_moving, dict(variety='array-nd'))

    filters_moving_bitmask = Cpt(
        EpicsSignalRO, ':SYS:FiltersMovingBitmask_RBV', kind='normal',
        doc='Filter-by-filter motion status as a bitmask',
    )
    set_metadata(filters_moving_bitmask, dict(variety='bitmask', bits=18))

    run_calculation = Cpt(
        EpicsSignal, ':SYS:Run', kind='config',
        doc='Start the calculation',
    )
    set_metadata(run_calculation, dict(variety='command-proc', value=1))

    apply_config = Cpt(
        EpicsSignal, ':SYS:ApplyConfiguration', kind='config',
        doc='Apply the best configuration (i.e., move the filters)',
    )
    set_metadata(apply_config, dict(variety='command-proc', value=1))

    moving = Cpt(
        EpicsSignalRO, ':SYS:Moving_RBV', kind='config',
        doc='Are filters being moved in/out?',
    )
    set_metadata(moving, dict(variety='bitmask', bits=1))

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.filters_by_index = {
            index: getattr(self.filters, attr)
            for index, attr in self._filter_index_to_attr.items()
        }

    def _bitmask_to_list(self, value):
        """Bitmask value to list of bits (e.g., 23 to [..., 1, 0, 1, 1, 1])."""
        bits = bin(value)[2:].zfill(self.num_filters)
        return list(int(i) for i in bits)

    def get_active_config(self, **kwargs):
        """Get the active filter configuration."""
        return self._bitmask_to_list(self.active_config_bitmask.get(**kwargs))

    def get_best_config(self, **kwargs):
        """Get the calculated (best) filter configuration."""
        return self._bitmask_to_list(self.best_config_bitmask.get(**kwargs))

    def get_moving_status(self, **kwargs):
        """Get the filter motion status."""
        return self._bitmask_to_list(self.filters_moving_bitmask.get(**kwargs))

    def calculate(self, transmission, *, energy=None, use_floor=True):
        """
        Calculate a blade configuration given a desired transmission value.

        If ``energy`` is not specified, this method defaults to using the
        current L-line photon energy, as reported by the Photon Machine
        Protection System: ``PMPS:LFE:PE:UND:CurrentPhotonEnergy_RBV``.

        Parameters
        ----------
        transmission : float
            The desired transmission, in the range [0, 1].

        energy : float, optional
            The photon energy to use for the calculation.

        use_floor : bool, optional
            Select floor or ceiling transmission estimation.  Defaults to
            floor.
        """

        if energy is not None:
            self.energy_source.put('Custom')
            self.energy_custom.put(float(energy))
        else:
            self.energy_source.put('Actual')

        self.calc_mode.put('Floor' if use_floor else 'Ceiling')
        self.desired_transmission.put(transmission)
        self.run_calculation.put(1, wait=True)
        return self.get_best_config(use_monitor=False)


class AttenuatorCalculator_AT2L0(AttenuatorCalculatorBase):
    """
    Solid attenuator variant from the LCLS-II XTES project.

    Parameters
    ----------
    prefix : str
        Full Solid Attenuator base PV.

    name : str
        Alias for the Solid Attenuator.
    """

    tab_component_names = True
    first_filter = 2
    num_filters = 18
    _filter_index_to_attr = {
        idx: f'filter_{idx:02d}' for idx in range(first_filter,
                                                  num_filters + first_filter)
    }

    # Creates filters from 2 to num_filters, with attributes filter_02 and so
    # on.
    filters = DDC(
        {attr: (AttenuatorCalculatorFilter,
                f':FILTER:{idx:02d}:',
                {'index': idx})
         for idx, attr in _filter_index_to_attr.items()
         }
    )


class AT2L0(FltMvInterface, PVPositionerPC, LightpathInOutMixin):
    """
    AT2L0 solid attenuator variant from the LCLS-II XTES project.

    Motorized, 18 filters + 1 inspection mirror.
    This class includes a calculator to aid in determining which filters to
    insert for a given attenuation at a specific energy.

    Parameters
    ----------
    prefix : str
        Solid Attenuator base PV.

    name : str
        Alias for the Solid Attenuator.
    """

    # QIcon for UX
    _icon = 'fa.barcode'
    tab_component_names = True

    # Register that all blades are needed for lightpath calc
    lightpath_cpts = [f'blade_{idx:02}' for idx in range(1, 20)]

    # Summary for lightpath view
    num_in = Cpt(InternalSignal, kind='hinted')
    num_out = Cpt(InternalSignal, kind='hinted')

    calculator = UCpt(AttenuatorCalculator_AT2L0)
    blade_01 = Cpt(FEESolidAttenuatorBlade, ':MMS:01')
    blade_02 = Cpt(FEESolidAttenuatorBlade, ':MMS:02')
    blade_03 = Cpt(FEESolidAttenuatorBlade, ':MMS:03')
    blade_04 = Cpt(FEESolidAttenuatorBlade, ':MMS:04')
    blade_05 = Cpt(FEESolidAttenuatorBlade, ':MMS:05')
    blade_06 = Cpt(FEESolidAttenuatorBlade, ':MMS:06')
    blade_07 = Cpt(FEESolidAttenuatorBlade, ':MMS:07')
    blade_08 = Cpt(FEESolidAttenuatorBlade, ':MMS:08')
    blade_09 = Cpt(FEESolidAttenuatorBlade, ':MMS:09')
    blade_10 = Cpt(FEESolidAttenuatorBlade, ':MMS:10')
    blade_11 = Cpt(FEESolidAttenuatorBlade, ':MMS:11')
    blade_12 = Cpt(FEESolidAttenuatorBlade, ':MMS:12')
    blade_13 = Cpt(FEESolidAttenuatorBlade, ':MMS:13')
    blade_14 = Cpt(FEESolidAttenuatorBlade, ':MMS:14')
    blade_15 = Cpt(FEESolidAttenuatorBlade, ':MMS:15')
    blade_16 = Cpt(FEESolidAttenuatorBlade, ':MMS:16')
    blade_17 = Cpt(FEESolidAttenuatorBlade, ':MMS:17')
    blade_18 = Cpt(FEESolidAttenuatorBlade, ':MMS:18')
    blade_19 = Cpt(FEESolidAttenuatorBlade, ':MMS:19')

    @property
    def setpoint(self):
        """(PVPositioner compat) - use desired transmission as setpoint."""
        return self.calculator.desired_transmission

    @property
    def readback(self):
        """(PVPositioner compat) - use actual transmission as readback."""
        return self.calculator.actual_transmission

    @property
    def actuate(self):
        """(PVPositioner compat) - use apply_config as an actuation signal."""
        return self.calculator.apply_config

    def _setup_move(self, position):
        """(PVPositioner compat) - calculate, then move."""
        self.calculator.calculate(position)
        return super()._setup_move(position)

    def __init__(self, *args, limits=None, **kwargs):
        UCpt.collect_prefixes(self, dict(calculator_prefix='AT2L0:CALC'))
        limits = limits or (0.0, 1.0)
        super().__init__(*args, limits=limits, **kwargs)

    def _set_lightpath_states(self, lightpath_values):
        info = super()._set_lightpath_states(lightpath_values)
        if info is not None:
            self.num_in.put(info['in_check'].count(True), force=True)
            self.num_out.put(info['out_check'].count(True), force=True)

    def format_status_info(self, status_info):
        """
        Override status info handler to render the att
        """
        # Get the attenuator statuses
        blade_states = []
        for cpt in self.lightpath_cpts:
            try:
                blade_states.append(
                    status_info[cpt]['state']['state']['value']
                )
            except KeyError:
                break

        lines = render_ascii_att(blade_states, start_index=1)
        try:
            calc = status_info['calculator']
            transmission = calc['actual_transmission']['value']
            transmission_3omega = calc['actual_transmission_3omega']['value']
            energy_actual = calc['energy_actual']['value']
        except KeyError:
            ...
        else:
            energy = energy_actual / 1e3
            energy_3omega = energy * 3.0
            lines.append(
                f'Transmission (E={energy:.3} keV): {transmission:.4E}'
            )
            lines.append(
                f'Transmission for 3rd harmonic (E={energy_3omega:.3} keV): '
                f'{transmission_3omega:.4E}'
            )

        return '\n'.join(lines)


FEESolidAttenuator = AT2L0  # back-compatibility


class BladeStateEnum(enum.Enum):
    Unknown = 0
    OUT = 1
    IN = 2
    STUCK_OUT = 3
    STUCK_IN = 4

    @property
    def as_out_row(self) -> str:
        """Returns ASCII information for "out" row representation."""
        return {
            BladeStateEnum.OUT: 'X',
            BladeStateEnum.IN: '',
            BladeStateEnum.STUCK_OUT: 'S',
            BladeStateEnum.STUCK_IN: '',
        }.get(self, '?')

    @property
    def as_in_row(self) -> str:
        """Returns ASCII information for "in" row representation."""
        return {
            BladeStateEnum.OUT: '',
            BladeStateEnum.IN: 'X',
            BladeStateEnum.STUCK_OUT: '',
            BladeStateEnum.STUCK_IN: 'S',
        }.get(self, '?')


def get_blade_enum(value):
    try:
        return BladeStateEnum[value]
    except KeyError:
        return BladeStateEnum(value)


def render_ascii_att(blade_states, *, start_index=0):
    """
    Creates the attenuator ascii art.

    Parameters
    ----------
    blade_states: list of BladeStateEnum
        The elements of this list represent the current blade states.

    start_index : int, optional
        The starting filter index.

    Returns
    -------
    ascii_lines: list of str
        The lines that should be printed to the screen.
    """
    filter_line = ['filter # ']
    out_line = [' OUT     ']
    in_line = [' IN      ']

    for idx, state in enumerate(blade_states, start_index):
        index_str = str(idx)
        filter_line.append(index_str)
        state_enum = get_blade_enum(state)
        out_line.append(state_enum.as_out_row.center(len(index_str)))
        in_line.append(state_enum.as_in_row.center(len(index_str)))

    separator = '|'
    return [separator.join(filter_line + ['']),
            separator.join(out_line + ['']),
            separator.join(in_line + [''])]
