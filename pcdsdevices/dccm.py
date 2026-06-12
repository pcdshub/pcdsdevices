from decimal import Decimal, getcontext
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from pcdsdevices.beam_stats import BeamEnergyRequest
from pcdsdevices.device import Device
from pcdsdevices.device import UpdateComponent as UpCpt
from pcdsdevices.epics_motor import BeckhoffAxis
from pcdsdevices.interface import FltMvInterface
from pcdsdevices.pmps import TwinCATStatePMPS
from typing import Union, Optional


class DCCMCrystal(FltMvInterface, PVPositioner):
    """
    Energy positioner interface for a Single crystal.

    Controls and monitors the energy, state, coefficients, and tracking metrics
    associated with an individual crystal in the DCCM system.

    Attributes
    ----------
    setpoint : Cpt
        The target energy setpoint signal in keV.
    readback : Cpt
        The current estimated energy readback signal in keV.
    actuate : Cpt
        Command signal to initiate the energy move sequence.
    done : Cpt
        Status signal indicating whether the motion sequence is complete.
    stop_signal : Cpt
        Signal used to abort current energy adjustments.
    reset : Cpt
        Command signal to reset faults or clear movement cycles.
    angle_offset : Cpt
        Angular offset adjustment value for tuning crystal geometry.
    ctrl_velo_bias_gain : Cpt
        Velocity bias gain modifier for the underlying controller.
    lat_const_scaler : Cpt
        Lattice constant scaling modifier.
    crystal_type : Cpt
        The identifier string or type index for the crystal material/cut.
    coeff : Cpt
        Calculated tracking coefficient.
    est_pos_delta : Cpt
        Calculated differnece between estimated position and goal.
    est_energy_delta : Cpt
        Calculated differnece between estimated energy and goal.
    est_energy : Cpt
        Calculated energy based on theta angle.
    state : Cpt
        Current operational state enum from EPICS.
    error : Cpt
        Boolean indicating an error status.
    warning : Cpt
        Boolean indicating an warning status.
    error_msg : Cpt
        Diagnostic string explaining the current error state.
    warning_msg : Cpt
        Diagnostic string explaining the current warning state.
    """

    setpoint = Cpt(EpicsSignal, ":CmdkeV_RBV", write_pv=":CmdkeV")
    readback = Cpt(EpicsSignalRO, ":EstEnergy_RBV")
    actuate = Cpt(EpicsSignal, ":CmdMoveEnergy_RBV", write_pv=":CmdMoveEnergy")
    done = Cpt(EpicsSignalRO, ":Done_RBV")
    stop_signal = Cpt(EpicsSignal, ":CmdStop", kind="normal")

    reset = Cpt(EpicsSignal, ":CmdReset_RBV", write_pv=":CmdReset")

    angle_offset = Cpt(EpicsSignal, ":AngleOffset_RBV", write_pv=":AngleOffset")
    ctrl_velo_bias_gain = Cpt(
        EpicsSignal, ":CtrlVeloBiasGain_RBV", write_pv=":CtrlVeloBiasGain"
    )
    lat_const_scaler = Cpt(
        EpicsSignal, ":LatConstScaler_RBV", write_pv=":LatConstScaler"
    )

    crystal_type = Cpt(EpicsSignal, ":Type_RBV", write_pv=":Type")

    coeff = Cpt(EpicsSignalRO, ":Coeff_RBV")
    est_pos_delta = Cpt(EpicsSignalRO, ":EstPosDelta_RBV")
    est_energy_delta = Cpt(EpicsSignalRO, ":EstEnergyDelta_RBV")
    est_energy = Cpt(EpicsSignalRO, ":EstEnergy_RBV")

    state = Cpt(EpicsSignalRO, ":State_RBV")

    error = Cpt(EpicsSignalRO, ":Error_RBV")
    warning = Cpt(EpicsSignalRO, ":Warning_RBV")

    error_msg = Cpt(EpicsSignalRO, ":ErrorMsg_RBV", string=True)
    warning_msg = Cpt(EpicsSignalRO, ":WarningMsg_RBV", string=True)

    def __init__(self, prefix="", *, limits=None, name=None, read_attrs=None,
                 configuration_attrs=None, parent=None,
                 egu="", axis_prefix: str = '', **kwargs):
        """
        Initialize the DCCMCrystal device instance.

        Parameters
        ----------
        prefix : str, optional
            The EPICS base PV prefix for this crystal instance.
        limits : tuple, optional
            Soft position limits (low, high) for the positioner.
        name : str, optional
            The name used for the device in data collection.
        read_attrs : list of str, optional
            Attributes to include in the `read()` sequence.
        configuration_attrs : list of str, optional
            Attributes to include in configuration logging.
        parent : Device, optional
            The parent Device instance if nested.
        egu : str, optional
            Engineering units identifier (e.g., 'keV').
        axis_prefix : str, optional
            Optional identifier prefix mapping back to physical motors.
        **kwargs : dict
            Additional arguments passed up to `PVPositioner` and `OphydObj`.
        """
        self.axis_prefix = axis_prefix
        super().__init__(prefix, limits=limits, name=name,
                         read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         parent=parent, egu=egu, **kwargs)

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        """
        Execute an energy move sequence to the designated target coordinate.

        Updates the setpoint, triggers execution, clears the command done aknowledgement,
        and waits for the final low state verification.

        Parameters
        ----------
        position : float or int
            Target energy destination in keV.
        wait : bool, optional
            If True, blocks code execution until the motion finishes completely.
        timeout : float, optional
            Maximum time allocation in seconds to wait for motion status switches.
        moved_cb : callable, optional
            Callback function invoked upon move cycle completion.
            Expected signature: `moved_cb(obj=self)`.

        Returns
        -------
        status_done_low : SubscriptionStatus
            Ophyd status tracking tracking token representing the back-end
            un-latching phase.
        """
        status_done_high = SubscriptionStatus(
            self.done,
            lambda value, old_value, **kwargs: value == 1,
            run=False,
        )
        self.setpoint.put(position, wait=True)
        self.actuate.put(1, wait=True)

        status_done_high.wait(timeout=timeout)

        self.reset.put(1, wait=True)

        status_done_low = SubscriptionStatus(
            self.done,
            lambda value, old_value, **kwargs: value == 0,
            run=True,
        )

        if wait:
            status_done_low.wait(timeout=timeout)

        if moved_cb is not None:
            status_done_low.add_callback(lambda *args,
                                         **kwargs: moved_cb(obj=self))

        return status_done_low


class DCCMEnergy(DCCMCrystal):
    axis_coupling_enable = Cpt(EpicsSignal, ":CTC:Coupled_RBV",
                               write_pv=":CTC:Coupled", kind="normal")

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        self.axis_coupling_enable.put(1)
        return super().move(position, wait, timeout, moved_cb)

    def couple_axis(self):
        self.axis_coupling_enable.put(1)

    def decouple_axis(self):
        self.axis_coupling_enable.put(0)


class DCCMEnergyWithVernier(DCCMEnergy):
    """
    DCCM energy motor and the vernier.

    Moves the DCCM theta based on the requested energy using the values
    of the calculation constants, and reports the current energy
    based on the motor's position.

    Also moves the vernier when a move is requested to the DCCM motor.
    Note that the vernier is in units of eV, while the energy
    calculations are in units of keV.

    Parameters
    ----------
    prefix : str
        The PV prefix of the theta motor, e.g. XPP:MON:MPZ:07A
    hutch : str, optional
        The hutch we're in. This informs us as to which vernier
        PVs to write to. If omitted, we can guess this from the
        prefix.
    """
    acr_energy = FCpt(BeamEnergyRequest, '{hutch}', kind='normal',
                      doc='Requests ACR to move the Vernier.')

    # These are duplicate warnings with main energy motor
    _enable_warn_constants: bool = False
    hutch: str

    def __init__(
        self,
        prefix: str,
        hutch: Optional[str] = None,
        **kwargs
    ):
        # Determine which hutch to use
        if hutch is not None:
            self.hutch = hutch
        elif 'TXI' in prefix:
            self.hutch = 'TXI'
        elif 'CXI' in prefix:
            self.hutch = 'CXI'
        elif 'MEC' in prefix:
            self.hutch = 'MEC'
        elif 'MFX' in prefix:
            self.hutch = 'MFX'
        elif 'XCS' in prefix:
            self.hutch = 'XCS'
        else:
            self.hutch = 'TST'
        super().__init__(prefix, **kwargs)

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        self.acr_energy.put(position * 1000)
        return super().move(position, wait, timeout, moved_cb)


class DCCMEnergyWithACRStatus(DCCMEnergyWithVernier):
    """
    CCM energy motor and ACR beam energy request with status.
    Note that in this case vernier indicates any ways that ACR will act on the
    photon energy request. This includes the Vernier, but can also lead to
    motion of the undulators or the K.

    Parameters
    ----------
    prefix : str
        The PV prefix of the Alio motor, e.g. XPP:MON:MPZ:07A
    hutch : str, optional
        The hutch we're in. This informs us as to which vernier
        PVs to write to. If omitted, we can guess this from the
        prefix.
    acr_status_sufix : str
        Prefix to the SIOC PV that ACR uses to report the move status.
        For HXR this usually is 'AO805'.
    """
    acr_energy = FCpt(BeamEnergyRequest, '{hutch}',
                      pv_index='{pv_index}',
                      acr_status_suffix='{acr_status_suffix}',
                      add_prefix=('suffix', 'write_pv', 'pv_index',
                                  'acr_status_suffix'),
                      kind='normal',
                      doc='Requests ACR to move the energy.')

    def __init__(
        self,
        prefix: str,
        hutch: Optional[str] = None,
        acr_status_suffix='AO805',
        pv_index=2,
        **kwargs
    ):
        self.acr_status_suffix = acr_status_suffix
        self.pv_index = pv_index
        super().__init__(prefix, hutch=hutch, **kwargs)


class DCCMTarget(TwinCATStatePMPS):
    config = UpCpt(state_count=2)
    _in_if_not_out = True


class DCCM(Device):
    """
    The full DCCM assembly.

    Double Channel Cut Monochrometer controlled with a Beckhoff PLC.
    This includes five axes in total:
        - 2 for crystal manipulation (TH1/Upstream and TH2/Downstream)
        - 1 for chamber translation in x direction (TX)
    - 2 for YAG diagnostics (TXD and TYD)
    """

    tab_component_names = True

    tx_state = Cpt(DCCMTarget, ':MMS:STATE', kind='hinted', doc='Control of TX axis via saved positions.')

    energy = FCpt(
        DCCMEnergy, '{self.prefix}', kind='hinted',
        crystal="01",
        doc=(
            'PseudoPositioner that moves the theta motors in '
            'terms of the calculated DCCM energy.'
        ),
    )

    energy_with_vernier = FCpt(
        DCCMEnergyWithVernier, '{self.prefix}', kind='normal',
        crystal="01",
        hutch='{hutch}',
        add_prefix=('suffix', 'write_pv', 'hutch'),
        doc=(
            'PseudoPositioner that moves the theta motor in '
            'terms of the calculated DCCM energy while '
            'also requesting a vernier move.'
        ),
    )
    energy_with_acr_status = FCpt(
        DCCMEnergyWithACRStatus, '{self.prefix}', kind='normal',
        crystal="01",
        hutch='{hutch}',
        pv_index='{acr_status_pv_index}',
        acr_status_suffix='{acr_status_suffix}',
        add_prefix=('suffix', 'write_pv', 'acr_status_suffix', 'pv_index', 'hutch'),
        doc=(
            'PseudoPositioner that moves the alio in '
            'terms of the calculated CCM energy while '
            'also requesting an energy change to ACR. '
            'This will wait on ACR to complete the move.'
        ),
    )

    th1 = Cpt(BeckhoffAxis, ":MMS:TH1", doc="Bragg Upstream/TH1 Axis", kind="normal")
    th2 = Cpt(BeckhoffAxis, ":MMS:TH2", doc="Bragg Downstream/TH2 Axis", kind="normal")
    tx = Cpt(BeckhoffAxis, ":MMS:TX", doc="Translation X Axis", kind="normal")
    txd = Cpt(BeckhoffAxis, ":MMS:TXD", doc="YAG Diagnostic X Axis", kind="normal")
    tyd = Cpt(BeckhoffAxis, ":MMS:TYD", doc="YAG Diagnostic Y Axis", kind="normal")

    crys_01 = Cpt(DCCMCrystal, '', crystal="01", kind="normal")
    crys_02 = Cpt(DCCMCrystal, '', crystal="02", kind="normal")

    lightpath_cpts = ['tx_state']

    def __init__(
            self,
            prefix: str,
            hutch: str = '',
            acr_status_suffix: str = 'AO805',
            acr_status_pv_index: int = 2,
            **kwargs
    ):
        self.hutch = hutch
        self.acr_status_suffix = acr_status_suffix
        self.acr_status_pv_index = acr_status_pv_index
        super().__init__(prefix, **kwargs)


    def _proxy_method(method_name):  # noqa
        """
        Proxy a method from tx_state
        """
        def method_selector(self, *args, **kwargs):
            return getattr(self.tx_state, method_name)(*args, **kwargs)

        return method_selector


    def _proxy_property(prop_name):  # noqa
        """Read-only property proxy for tx_state"""
        def getter(self):
            return getattr(self.tx_state, prop_name)

        # Only support read-only properties for now.
        return property(getter)

    inserted = _proxy_property('inserted')
    check_inserted = _proxy_method('check_inserted')
    removed = _proxy_property('removed')
    check_removed = _proxy_method('check_removed')
    insert = _proxy_method('insert')
    remove = _proxy_method('remove')

    def generate_scan_points(self,
                             start: Union[int, float, Decimal],
                             end: Union[int, float, Decimal],
                             step: Union[int, float, Decimal],
                             bidirectional: bool):
        if start < 0 or end < 0 < step < 0:
            raise ValueError("start, end and step size must be positive numbers")
        if start >= end:
            raise ValueError("invalid start and/or end points")
        if step >= start or step >= end:
            raise ValueError("invalid step size")

        getcontext().prec = 9

        start = Decimal(start)
        end = Decimal(end)
        step = Decimal(step)

        # Generate positions in the forward direction
        pos = start
        while pos <= end:
            yield pos
            pos += step

        if bidirectional:
            # Generate positions in the backward direction
            pos = end - step
            while pos >= start:
                yield pos
                pos -= step
