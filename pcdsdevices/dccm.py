from typing import Optional

from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal, EpicsSignalRO, InternalSignal
from ophyd.status import SubscriptionStatus

from pcdsdevices.beam_stats import BeamEnergyRequest
from pcdsdevices.device import GroupDevice
from pcdsdevices.device import UpdateComponent as UpCpt
from pcdsdevices.epics_motor import BeckhoffAxis
from pcdsdevices.interface import BaseInterface, FltMvInterface, LightpathInOutCptMixin
from pcdsdevices.pmps import TwinCATStatePMPS
from pcdsdevices.signal import PytmcSignal
from pcdsdevices.utils import measure_time


class DCCMCrystal(FltMvInterface, PVPositioner):
    """
    Energy positioner interface for a single crystal.

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

    _extra_sig_md = {
        "precision": 9,
        "units": "kev",
    }

    high_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="omitted",
    )

    low_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="omitted",
    )

    high_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="omitted",
        doc="The upper energy travel limit in keV.",
    )

    low_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="omitted",
        doc="The lower energy travel limit in keV.",
    )

    setpoint = Cpt(
        PytmcSignal,
        ":CmdkeV",
        io="io",
        doc="The target energy setpoint signal in keV.",
    )

    readback = Cpt(
        EpicsSignalRO,
        ":EstEnergy_RBV",
        doc="The current estimated energy readback signal in keV.",
    )

    actuate = Cpt(
        PytmcSignal,
        ":CmdMoveEnergy",
        io="io",
        doc="Command signal to initiate the energy move sequence.",
    )

    done = Cpt(
        EpicsSignalRO,
        ":Done_RBV",
        doc="Status signal indicating whether the motion sequence is complete.",
    )
    stop_signal = Cpt(
        EpicsSignal,
        ":CmdStop",
        kind="normal",
        doc="Signal used to abort current energy adjustments.",
    )

    reset = Cpt(
        PytmcSignal,
        ":CmdReset",
        io="io",
        doc="Command signal to reset faults or clear movement cycles.",
    )

    angle_offset = Cpt(
        PytmcSignal,
        ":AngleOffset",
        io="io",
        doc="Angular offset adjustment value for tuning crystal geometry.",
    )

    ctrl_velo_bias_gain = Cpt(
        PytmcSignal,
        ":CtrlVeloBiasGain",
        io="io",
        doc="Velocity bias gain modifier for the underlying controller.",
    )

    lat_const_scaler = Cpt(
        PytmcSignal,
        ":LatConstScaler",
        io="io",
        doc="Lattice constant scaling modifier.",
    )

    crystal_type = Cpt(
        PytmcSignal,
        ":Type",
        io="io",
        doc="The identifier string or type index for the crystal material/cut.",
    )

    coeff = Cpt(
        EpicsSignalRO,
        ":Coeff_RBV",
        doc="Calculated tracking coefficient.",
    )

    est_pos_delta = Cpt(
        EpicsSignalRO,
        ":EstPosDelta_RBV",
        kind="hinted",
        doc="Calculated difference between estimated position and goal.",
    )

    est_energy_delta = Cpt(
        EpicsSignalRO,
        ":EstEnergyDelta_RBV",
        kind="hinted",
        doc="Calculated difference between estimated energy and goal.",
    )

    est_energy = Cpt(
        EpicsSignalRO,
        ":EstEnergy_RBV",
        doc="Calculated energy based on theta angle.",
    )

    state = Cpt(
        EpicsSignalRO,
        ":State_RBV",
        doc="Current operational state enum from EPICS.",
    )

    error = Cpt(
        EpicsSignalRO,
        ":Error_RBV",
        doc="Boolean indicating an error status.",
    )

    warning = Cpt(
        EpicsSignalRO,
        ":Warning_RBV",
        doc="Boolean indicating a warning status.",
    )

    error_msg = Cpt(
        EpicsSignalRO,
        ":ErrorMsg_RBV",
        string=True,
        doc="Diagnostic string explaining the current error state.",
    )

    warning_msg = Cpt(
        EpicsSignalRO,
        ":WarningMsg_RBV",
        string=True,
        doc="Diagnostic string explaining the current warning state.",
    )

    def move(self, position, wait=True, timeout=10.0, moved_cb=None):
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

        self.reset.put(1, wait=True)
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
            status_done_low.add_callback(lambda *args, **kwargs: moved_cb(obj=self))

        return status_done_low


class DCCMEnergy(DCCMCrystal):
    axis_coupling_enable = FCpt(
        PytmcSignal,
        "{self._base_prefix}:CTC:Coupled",
        io="io",
        kind="hinted",
    )

    def __init__(self, prefix, *, crystal="01", **kwargs):
        self._base_prefix = prefix.rstrip(":")
        self.crystal = int(crystal)

        super().__init__(
            f"{self._base_prefix}:CTC:CRYS:{self.crystal:02d}",
            **kwargs,
        )

    @measure_time
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        self.couple_axis()
        return super().move(
            position,
            wait=wait,
            timeout=timeout,
            moved_cb=moved_cb,
        )

    def _proxy_method(method_name, *fixed_args):  # noqa
        """Proxy a signal method with predefined positional arguments."""

        def method_selector(self, *args, **kwargs):
            return getattr(self.axis_coupling_enable, method_name)(*fixed_args, *args, **kwargs)

        return method_selector

    couple_axis = _proxy_method("put", 1)
    decouple_axis = _proxy_method("put", 0)


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

    acr_energy = FCpt(BeamEnergyRequest, "{hutch}", kind="hinted", doc="Requests ACR to move the Vernier.")

    # These are duplicate warnings with main energy motor
    _enable_warn_constants: bool = False
    hutch: str

    def __init__(self, prefix: str, hutch: Optional[str] = None, **kwargs):
        # Determine which hutch to use
        if hutch is not None:
            self.hutch = hutch
        elif "TXI" in prefix:
            self.hutch = "TXI"
        elif "CXI" in prefix:
            self.hutch = "CXI"
        elif "MEC" in prefix:
            self.hutch = "MEC"
        elif "MFX" in prefix:
            self.hutch = "MFX"
        elif "XCS" in prefix:
            self.hutch = "XCS"
        else:
            self.hutch = "TST"
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

    acr_energy = FCpt(
        BeamEnergyRequest,
        "{hutch}",
        pv_index="{pv_index}",
        acr_status_suffix="{acr_status_suffix}",
        add_prefix=("suffix", "write_pv", "pv_index", "acr_status_suffix"),
        kind="hinted",
        doc="Requests ACR to move the energy.",
    )

    def __init__(self, prefix: str, hutch: Optional[str] = None, acr_status_suffix="AO805", pv_index=2, **kwargs):
        self.acr_status_suffix = acr_status_suffix
        self.pv_index = pv_index
        super().__init__(prefix, hutch=hutch, **kwargs)


class DCCMTarget(TwinCATStatePMPS):
    config = UpCpt(state_count=2)
    _in_if_not_out = True


class DCCM(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """
    The full DCCM assembly.

    Double Channel Cut Monochrometer controlled with a Beckhoff PLC.
    This includes five axes in total:
        - 2 for crystal manipulation (TH1/Upstream and TH2/Downstream)
        - 1 for chamber translation in x direction (TX)
    - 2 for YAG diagnostics (TXD and TYD)
    """

    tab_component_names = True

    tx_state = Cpt(DCCMTarget, ":MMS:STATE", kind="hinted", doc="Control of TX axis via saved positions.")

    energy = Cpt(
        DCCMEnergy,
        "",
        kind="hinted",
        doc=("PseudoPositioner that moves the theta motors in terms of the calculated DCCM energy."),
    )

    energy_with_vernier = FCpt(
        DCCMEnergyWithVernier,
        "{self.prefix}",
        kind="normal",
        hutch="{hutch}",
        add_prefix=("suffix", "write_pv", "hutch"),
        doc=(
            "PseudoPositioner that moves the theta motor in "
            "terms of the calculated DCCM energy while "
            "also requesting a vernier move."
        ),
    )
    energy_with_acr_status = FCpt(
        DCCMEnergyWithACRStatus,
        "{self.prefix}",
        kind="normal",
        hutch="{hutch}",
        pv_index="{acr_status_pv_index}",
        acr_status_suffix="{acr_status_suffix}",
        add_prefix=("suffix", "write_pv", "acr_status_suffix", "pv_index", "hutch"),
        doc=(
            "PseudoPositioner that moves the alio in "
            "terms of the calculated CCM energy while "
            "also requesting an energy change to ACR. "
            "This will wait on ACR to complete the move."
        ),
    )

    th1 = Cpt(BeckhoffAxis, ":MMS:TH1", doc="Bragg Upstream/TH1 Axis", kind="normal")
    th2 = Cpt(BeckhoffAxis, ":MMS:TH2", doc="Bragg Downstream/TH2 Axis", kind="normal")
    tx = Cpt(BeckhoffAxis, ":MMS:TX", doc="Translation X Axis", kind="normal")
    txd = Cpt(BeckhoffAxis, ":MMS:TXD", doc="YAG Diagnostic X Axis", kind="normal")
    tyd = Cpt(BeckhoffAxis, ":MMS:TYD", doc="YAG Diagnostic Y Axis", kind="normal")

    crys_01 = Cpt(DCCMCrystal, ":CTC:CRYS:01", kind="normal")
    crys_02 = Cpt(DCCMCrystal, ":CTC:CRYS:02", kind="normal")

    lightpath_cpts = ["tx_state"]

    def __init__(
        self, prefix: str, hutch: str = "", acr_status_suffix: str = "AO805", acr_status_pv_index: int = 2, **kwargs
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

    inserted = _proxy_property("inserted")
    check_inserted = _proxy_method("check_inserted")
    removed = _proxy_property("removed")
    check_removed = _proxy_method("check_removed")
    insert = _proxy_method("insert")
    remove = _proxy_method("remove")
