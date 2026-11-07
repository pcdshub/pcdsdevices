from __future__ import annotations

import math
import threading
from operator import index
from time import monotonic
from typing import Callable, Optional

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal, EpicsSignalRO, InternalSignal, Signal
from ophyd.status import MoveStatus, SubscriptionStatus

from pcdsdevices.beam_stats import BeamEnergyRequest
from pcdsdevices.device import GroupDevice
from pcdsdevices.device import UpdateComponent as UpCpt
from pcdsdevices.epics_motor import BeckhoffAxis
from pcdsdevices.interface import (
    BaseInterface,
    FltMvInterface,
    LightpathInOutCptMixin,
)
from pcdsdevices.pmps import TwinCATStatePMPS
from pcdsdevices.signal import PytmcSignal
from pcdsdevices.utils import measure_time

MovedCallback = Optional[Callable[..., None]]


_HUTCH_NAMES = ("L", "XCS", "CXI", "MEC", "MFX", "XPP")


def resolve_hutch(prefix: str, hutch: Optional[str] = None) -> str:
    """Resolve and validate a hutch name.

    An explicit hutch takes precedence. Otherwise, inspect colon-delimited
    tokens in the PV prefix.

    Raises
    ------
    ValueError
        If the explicit hutch is invalid, or the prefix does not identify
        a known hutch.
    """
    if hutch is not None and str(hutch).strip():
        name = str(hutch).strip().upper()
        if name not in _HUTCH_NAMES:
            raise ValueError(f"Unknown hutch {hutch!r}; choose one of {_HUTCH_NAMES}")
        return name

    prefix_tokens = {token.upper() for token in prefix.strip(":").split(":")}

    for candidate in _HUTCH_NAMES:
        if candidate in prefix_tokens:
            return candidate

    raise ValueError(f"Cannot determine ACR hutch from prefix {prefix!r}; pass hutch explicitly")


class HutchSelectionSignal(Signal):
    """Writable enum signal for a Typhos hutch dropdown.

    The stored value is an integer enum index. Python callers may write
    either a hutch name or its index.

    This is an operator-selected destination, not a readback of physical
    beam routing. Its value is local to this Python process.
    """

    enum_strs = _HUTCH_NAMES

    def __init__(self, *args, value=0, **kwargs):
        metadata = dict(kwargs.pop("metadata", None) or {})
        metadata["enum_strs"] = self.enum_strs

        super().__init__(
            *args,
            value=self._normalize(value),
            metadata=metadata,
            **kwargs,
        )

    @classmethod
    def _normalize(cls, value) -> int:
        if isinstance(value, str):
            name = value.strip().upper()
            try:
                return cls.enum_strs.index(name)
            except ValueError as exc:
                raise ValueError(f"Unknown hutch {value!r}; choose one of {cls.enum_strs}") from exc

        try:
            value = index(value)
        except TypeError as exc:
            raise ValueError("Hutch must be a hutch name or an integer enum index") from exc

        if not 0 <= value < len(cls.enum_strs):
            raise ValueError(f"Invalid hutch index: {value}")

        return value

    def check_value(self, value):
        self._normalize(value)

    def put(self, value, **kwargs):
        return super().put(self._normalize(value), **kwargs)

    @property
    def selected_name(self) -> str:
        """Currently selected hutch name."""
        return self.enum_strs[int(self.get())]

    def describe(self):
        description = super().describe()
        description[self.name]["enum_strs"] = self.enum_strs
        return description


class DCCMACRRequests(Device):
    """ACR request devices indexed by destination hutch.

    Individual devices are lazy: selecting a hutch creates its request
    device on first access.

    Keeping separate devices avoids attempting to retarget the EPICS
    signals of an already-created BeamEnergyRequest.
    """

    cxi = FCpt(BeamEnergyRequest, "CXI", lazy=True, kind="normal")
    mec = FCpt(BeamEnergyRequest, "MEC", lazy=True, kind="normal")
    mfx = FCpt(BeamEnergyRequest, "MFX", lazy=True, kind="normal")
    xcs = FCpt(BeamEnergyRequest, "XCS", lazy=True, kind="normal")
    xpp = FCpt(BeamEnergyRequest, "XPP", lazy=True, kind="normal")

    def __init__(
        self,
        prefix="",
        *,
        pv_index=2,
        acr_status_suffix="AO805",
        **kwargs,
    ):
        self.pv_index = int(pv_index)
        self.acr_status_suffix = acr_status_suffix
        super().__init__(prefix, **kwargs)

    def for_hutch(self, hutch: str):
        """Return the request device for a validated hutch name."""
        name = resolve_hutch("", hutch)
        return getattr(self, name.lower())


_ACR_STATUS_COMPONENT_KWARGS = {
    "pv_index": "{self.pv_index}",
    "acr_status_suffix": "{self.acr_status_suffix}",
    "add_prefix": ("suffix", "pv_index", "acr_status_suffix"),
}


class DCCMACRRequestsWithStatus(DCCMACRRequests):
    """Hutch-specific ACR request devices that monitor completion."""

    cxi = UpCpt(**_ACR_STATUS_COMPONENT_KWARGS)
    mec = UpCpt(**_ACR_STATUS_COMPONENT_KWARGS)
    mfx = UpCpt(**_ACR_STATUS_COMPONENT_KWARGS)
    xcs = UpCpt(**_ACR_STATUS_COMPONENT_KWARGS)
    xpp = UpCpt(**_ACR_STATUS_COMPONENT_KWARGS)


class DCCMCrystal(FltMvInterface, PVPositioner):
    """Energy positioner interface for a single DCCM crystal.

    Controls and monitors energy, state, coefficients, and tracking
    metrics associated with an individual crystal.
    """

    DEFAULT_MOVE_TIMEOUT = 10.0
    DONE_HIGH_VALUE = 1
    DONE_LOW_VALUE = 0
    RESET_VALUE = 1
    ACTUATE_VALUE = 1
    STOP_VALUE = 1

    _extra_sig_md = {
        "precision": 9,
        "units": "keV",
    }

    high_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="config",
    )

    low_limit_travel = Cpt(
        InternalSignal,
        metadata=_extra_sig_md,
        kind="config",
    )

    setpoint = Cpt(
        PytmcSignal,
        ":CmdkeV",
        io="io",
        kind="normal",
        doc="The target energy setpoint signal in keV.",
    )

    readback = Cpt(
        EpicsSignalRO,
        ":EstEnergy_RBV",
        kind="hinted",
        doc="The current estimated energy readback signal in keV.",
    )

    user_readback = Cpt(
        EpicsSignalRO,
        ":EstEnergy_RBV",
        kind="omitted",
    )

    actuate = Cpt(
        PytmcSignal,
        ":CmdMoveEnergy",
        io="io",
        kind="omitted",
        doc="Command signal to initiate the energy move sequence.",
    )

    done = Cpt(
        EpicsSignalRO,
        ":Done_RBV",
        kind="normal",
        doc="PLC completion acknowledgement used by the move handshake.",
    )

    stop_signal = Cpt(
        EpicsSignal,
        ":CmdStop",
        kind="omitted",
        doc="Command signal to abort current energy adjustments.",
    )

    reset = Cpt(
        PytmcSignal,
        ":CmdReset",
        io="io",
        kind="omitted",
        doc="Command signal to reset faults or clear movement cycles.",
    )

    angle_offset = Cpt(
        PytmcSignal,
        ":AngleOffset",
        io="io",
        kind="config",
        doc="Angular offset adjustment value for tuning crystal geometry.",
    )

    ctrl_velo_bias_gain = Cpt(
        PytmcSignal,
        ":CtrlVeloBiasGain",
        io="io",
        kind="config",
        doc="Velocity bias gain modifier for the underlying controller.",
    )

    lat_const_scaler = Cpt(
        PytmcSignal,
        ":LatConstScaler",
        io="io",
        kind="config",
        doc="Lattice constant scaling modifier.",
    )

    crystal_type = Cpt(
        PytmcSignal,
        ":Type",
        io="io",
        kind="config",
        doc="The identifier string or type index for the crystal material/cut.",
    )

    coeff = Cpt(
        EpicsSignalRO,
        ":Coeff_RBV",
        kind="normal",
        doc="Calculated tracking coefficient.",
    )

    est_pos_delta = Cpt(
        EpicsSignalRO,
        ":EstPosDelta_RBV",
        kind="hinted",
        doc="Difference between estimated position and goal.",
    )

    est_energy_delta = Cpt(
        EpicsSignalRO,
        ":EstEnergyDelta_RBV",
        kind="hinted",
        doc="Difference between estimated energy and goal.",
    )

    est_energy = Cpt(
        EpicsSignalRO,
        ":EstEnergy_RBV",
        kind="omitted",
        doc="Alias of the estimated energy readback.",
    )

    state = Cpt(
        EpicsSignalRO,
        ":State_RBV",
        kind="normal",
        doc="Current operational state enum from EPICS.",
    )

    error = Cpt(
        EpicsSignalRO,
        ":Error_RBV",
        kind="normal",
        doc="Boolean indicating an error status.",
    )

    warning = Cpt(
        EpicsSignalRO,
        ":Warning_RBV",
        kind="normal",
        doc="Boolean indicating a warning status.",
    )

    error_msg = Cpt(
        EpicsSignalRO,
        ":ErrorMsg_RBV",
        string=True,
        kind="normal",
        doc="Diagnostic string explaining the current error state.",
    )

    warning_msg = Cpt(
        EpicsSignalRO,
        ":WarningMsg_RBV",
        string=True,
        kind="normal",
        doc="Diagnostic string explaining the current warning state.",
    )

    def __init__(self, *args, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.DEFAULT_MOVE_TIMEOUT

        super().__init__(*args, **kwargs)

        self._move_lock = threading.RLock()
        self._active_move_status = None
        self._moving_from_this_device = False

        if self.limits is not None:
            low, high = self.limits
            self.low_limit_travel.put(low, force=True, internal=True)
            self.high_limit_travel.put(high, force=True, internal=True)

    @property
    def moving(self) -> bool:
        """Whether this Python device currently has an active move.

        Done_RBV uses zero for both idle and moving states, so this
        property tracks only moves initiated through this instance.
        """
        return self._moving_from_this_device

    def check_value(self, position):
        """Validate a requested energy and enforce configured soft limits."""
        try:
            position = float(position)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Energy must be a finite number; received {position!r}") from exc

        if not math.isfinite(position):
            raise ValueError(f"Energy must be finite; received {position!r}")

        return super().check_value(position)

    def check_error(self) -> None:
        """Raise if the PLC currently reports an error."""
        if bool(self.error.get()):
            message = self.error_msg.get() or "DCCM PLC reports an error"
            raise RuntimeError(str(message))

    @staticmethod
    def _stage_exception(stage_status, message: str) -> Exception:
        """Get a failed stage's exception, with a fallback message."""
        try:
            exc = stage_status.exception(timeout=0)
        except Exception as exc_from_status:
            return exc_from_status

        return exc or RuntimeError(message)

    def _resolve_timeout(self, timeout: Optional[float]) -> float:
        """Resolve and validate the total move timeout."""
        if timeout is None:
            timeout = self.timeout
        if timeout is None:
            timeout = self.DEFAULT_MOVE_TIMEOUT

        timeout = float(timeout)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError(f"Move timeout must be a positive finite number, got {timeout!r}")

        return timeout

    def _add_moved_callback(self, status, moved_cb: MovedCallback) -> None:
        """Attach the legacy moved_cb(obj=self) callback convention."""
        if moved_cb is not None:
            status.add_callback(lambda _status: moved_cb(obj=self))

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        """Request an energy move and return its complete handshake status.

        With wait=False, return after issuing the command writes. The
        returned status completes only after Done_RBV transitions high
        and then low following reset acknowledgement.

        Parameters
        ----------
        position : float
            Target energy in keV.
        wait : bool, optional
            Wait for the returned status before returning.
        timeout : float, optional
            Total timeout for both PLC handshake phases.
        moved_cb : callable, optional
            Called as moved_cb(obj=self) when the overall status completes.

        Returns
        -------
        ophyd.status.MoveStatus
            Status representing the entire PLC handshake.
        """
        self.check_value(position)
        position = float(position)
        self.check_error()
        timeout = self._resolve_timeout(timeout)

        with self._move_lock:
            if self._active_move_status is not None and not self._active_move_status.done:
                raise RuntimeError(f"{self.name} already has an active move")

            move_status = MoveStatus(self, position, timeout=timeout)
            self._active_move_status = move_status
            self._moving_from_this_device = True

        deadline = monotonic() + timeout
        stage_statuses = []
        error_callback = None

        def set_move_exception(exc: Exception) -> None:
            if not move_status.done:
                move_status.set_exception(exc)

        def remaining_time() -> float:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError(f"{self.name} move timed out during PLC handshake")
            return remaining

        def on_error(*, value, **kwargs):
            if bool(value) and not move_status.done:
                try:
                    message = self.error_msg.get()
                except Exception:
                    message = ""

                set_move_exception(
                    RuntimeError(str(message) if message else "DCCM PLC reported an error during motion")
                )

        def finalize(_status):
            # Remove error monitoring and unfinished handshake subscriptions.
            if error_callback is not None:
                try:
                    self.error.clear_sub(error_callback)
                except Exception:
                    pass

            for stage_status in tuple(stage_statuses):
                if not stage_status.done:
                    try:
                        stage_status.set_exception(
                            RuntimeError("Overall DCCM move ended before this handshake stage completed")
                        )
                    except Exception:
                        pass

            with self._move_lock:
                if self._active_move_status is move_status:
                    self._active_move_status = None
                    self._moving_from_this_device = False

        move_status.add_callback(finalize)

        def on_done_low(stage_status):
            if move_status.done:
                return

            if not stage_status.success:
                set_move_exception(
                    self._stage_exception(
                        stage_status,
                        "DCCM acknowledgement-clear phase failed",
                    )
                )
                return

            try:
                self.check_error()
            except Exception as exc:
                set_move_exception(exc)
                return

            move_status.set_finished()

        def on_done_high(stage_status):
            if move_status.done:
                return

            if not stage_status.success:
                set_move_exception(
                    self._stage_exception(
                        stage_status,
                        "DCCM move-completion phase failed",
                    )
                )
                return

            try:
                self.check_error()

                # Subscribe before reset to avoid missing a fast transition.
                done_low_status = SubscriptionStatus(
                    self.done,
                    lambda *, value, **kwargs: value == self.DONE_LOW_VALUE,
                    run=False,
                    timeout=remaining_time(),
                )
                stage_statuses.append(done_low_status)
                done_low_status.add_callback(on_done_low)

                self.reset.put(self.RESET_VALUE, wait=True)
            except Exception as exc:
                set_move_exception(exc)

        error_callback = on_error
        self.error.subscribe(error_callback, run=True)
        if move_status.done:
            if wait:
                move_status.wait()
            return move_status

        try:
            # Subscribe before commands to avoid missing Done=1.
            done_high_status = SubscriptionStatus(
                self.done,
                lambda *, value, **kwargs: value == self.DONE_HIGH_VALUE,
                run=False,
                timeout=timeout,
            )
            stage_statuses.append(done_high_status)
            done_high_status.add_callback(on_done_high)

            # Preserve the established PLC command sequence.
            # Confirm reset edge/level semantics in TwinCAT.
            self.reset.put(self.RESET_VALUE, wait=True)
            self.setpoint.put(position, wait=True)
            self.actuate.put(self.ACTUATE_VALUE, wait=True)
        except Exception as exc:
            set_move_exception(exc)

        self._add_moved_callback(move_status, moved_cb)

        if wait:
            move_status.wait()

        return move_status

    def stop(self, *, success=False):
        """Issue PLC stop and finish any active software move status."""
        active_status = self._active_move_status

        try:
            self.stop_signal.put(self.STOP_VALUE, wait=True)
        except Exception as exc:
            if active_status is not None and not active_status.done:
                active_status.set_exception(exc)
            raise

        if active_status is not None and not active_status.done:
            if success:
                active_status.set_finished()
            else:
                active_status.set_exception(RuntimeError(f"{self.name} move stopped"))


class DCCMEnergy(DCCMCrystal):
    """DCCM crystal energy positioner with theta-axis coupling."""

    axis_coupling_enable = FCpt(
        PytmcSignal,
        "{self._base_prefix}:CTC:Coupled",
        io="io",
        kind="omitted",
        doc="Command to enable/disable crystal-axis coupling.",
    )

    def __init__(self, prefix, *, crystal="01", **kwargs):
        self._base_prefix = prefix.rstrip(":")
        self.crystal = int(crystal)

        super().__init__(
            f"{self._base_prefix}:CTC:CRYS:{self.crystal:02d}",
            **kwargs,
        )

    def _prepare_move(self, position):
        """Validate the move and enable coupling before issuing motion."""
        self.check_value(position)
        self.check_error()

        # This waits for the write, not a separate PLC coupling readback.
        self.couple_axis(wait=True)

    @measure_time
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        self._prepare_move(position)
        return super().move(
            position,
            wait=wait,
            timeout=timeout,
            moved_cb=moved_cb,
        )

    @staticmethod
    def _proxy_method(method_name, *fixed_args):
        """Proxy a signal method with predefined positional arguments."""

        def method_selector(self, *args, **kwargs):
            return getattr(self.axis_coupling_enable, method_name)(
                *fixed_args,
                *args,
                **kwargs,
            )

        return method_selector

    couple_axis = _proxy_method("put", 1)
    decouple_axis = _proxy_method("put", 0)


class DCCMEnergyWithVernier(DCCMEnergy):
    """DCCM energy motor that also requests a Vernier/ACR energy change.

    The hutch component is an enum dropdown selecting the ACR destination.

    DCCM energy is specified in keV; the ACR request is specified in eV.
    Both move statuses are combined. For the no-wait ACR variant, the ACR
    status may complete once the request is accepted, rather than when
    the physical beam-energy change has completed.

    Changing the selection affects subsequent requests only. It does not
    redirect an in-progress request or change physical beam routing.
    """

    hutch = Cpt(
        HutchSelectionSignal,
        value=0,
        kind="config",
        doc="Selected beam destination / ACR request hutch.",
    )

    acr_requests = Cpt(
        DCCMACRRequests,
        "",
        kind="normal",
        doc="ACR request devices for the available hutches.",
    )

    _enable_warn_constants: bool = False

    def __init__(self, prefix: str, hutch: Optional[str] = None, **kwargs):
        initial_hutch = resolve_hutch(prefix, hutch)
        super().__init__(prefix, **kwargs)
        self.hutch.put(initial_hutch)

    @property
    def hutch_name(self) -> str:
        """Currently selected destination."""
        return self.hutch.selected_name

    @property
    def acr_energy(self):
        """ACR request device for the currently selected hutch."""
        return self.acr_requests.for_hutch(self.hutch_name)

    def move(self, position, wait=True, timeout=None, moved_cb=None):
        self._prepare_move(position)
        position = float(position)
        timeout = self._resolve_timeout(timeout)

        # Capture the selected request device once for this move.
        # Later dropdown changes cannot retarget this request.
        acr_energy = self.acr_energy

        # Request ACR first, preserving the original command ordering.
        acr_status = acr_energy.move(
            position * 1000.0,
            wait=False,
            timeout=timeout,
        )

        try:
            dccm_status = DCCMCrystal.move(
                self,
                position,
                wait=False,
                timeout=timeout,
                moved_cb=None,
            )
        except Exception as exc:
            # There is no generic cancellation command for an ACR request
            # that has already been accepted.
            raise RuntimeError("DCCM move failed to start after the ACR energy request was issued") from exc

        combined_status = acr_status & dccm_status
        self._add_moved_callback(combined_status, moved_cb)

        if wait:
            combined_status.wait()

        return combined_status


class DCCMEnergyWithACRStatus(DCCMEnergyWithVernier):
    """DCCM energy positioner that waits for ACR completion.

    acr_status_suffix selects the SIOC completion PV used by
    BeamEnergyRequest. That PV is expected to be zero while moving and
    one when complete.
    """

    acr_requests = FCpt(
        DCCMACRRequestsWithStatus,
        "{self.prefix}",
        pv_index="{self.pv_index}",
        acr_status_suffix="{self.acr_status_suffix}",
        add_prefix=("suffix", "pv_index", "acr_status_suffix"),
        kind="normal",
        doc="Hutch-specific ACR requests with completion monitoring.",
    )

    def __init__(
        self,
        prefix: str,
        hutch: Optional[str] = None,
        acr_status_suffix: str = "AO805",
        pv_index: int = 2,
        **kwargs,
    ):
        self.acr_status_suffix = acr_status_suffix
        self.pv_index = int(pv_index)
        super().__init__(prefix, hutch=hutch, **kwargs)


class DCCMTarget(TwinCATStatePMPS):
    """PMPS target state for the DCCM translation axis."""

    config = UpCpt(state_count=2)
    _in_if_not_out = True


class DCCM(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """Full DCCM assembly with a selectable ACR destination.

    The assembly includes two crystal manipulation axes, chamber
    translation, and two YAG diagnostic axes.

    The hutch dropdown is synchronized with both ACR-enabled energy
    interfaces. Editing any of those dropdowns updates the others.

    This selection records the operator-selected destination; it neither
    detects nor changes physical beam routing.
    """

    tab_component_names = True
    energy_limits = (4.0, 25.0)

    hutch = Cpt(
        HutchSelectionSignal,
        value=0,
        kind="config",
        doc="Selected beam destination / ACR request hutch.",
    )

    tx_state = Cpt(
        DCCMTarget,
        ":MMS:STATE",
        kind="hinted",
        doc="Control of TX axis via saved positions.",
    )

    tx = Cpt(
        BeckhoffAxis,
        ":MMS:TX",
        doc="Translation X Axis",
        kind="normal",
    )

    energy = Cpt(
        DCCMEnergy,
        "",
        kind="hinted",
        limits=energy_limits,
        doc="Moves the theta motors in terms of calculated DCCM energy.",
    )

    energy_with_vernier = FCpt(
        DCCMEnergyWithVernier,
        "{self.prefix}",
        kind="normal",
        limits=energy_limits,
        hutch="{self._initial_hutch}",
        add_prefix=("suffix", "write_pv", "hutch"),
        doc=(
            "Moves the DCCM theta motor in terms of calculated energy "
            "while also requesting a Vernier move for the selected hutch."
        ),
    )

    energy_with_acr_status = FCpt(
        DCCMEnergyWithACRStatus,
        "{self.prefix}",
        kind="normal",
        limits=energy_limits,
        hutch="{self._initial_hutch}",
        pv_index="{self.acr_status_pv_index}",
        acr_status_suffix="{self.acr_status_suffix}",
        add_prefix=(
            "suffix",
            "write_pv",
            "acr_status_suffix",
            "pv_index",
            "hutch",
        ),
        doc=(
            "Moves the DCCM energy while requesting an ACR energy "
            "change for the selected hutch and waiting for completion."
        ),
    )

    crys_01 = Cpt(
        DCCMCrystal,
        ":CTC:CRYS:01",
        kind="normal",
        limits=energy_limits,
    )

    crys_02 = Cpt(
        DCCMCrystal,
        ":CTC:CRYS:02",
        kind="normal",
        limits=energy_limits,
    )

    th1 = Cpt(
        BeckhoffAxis,
        ":MMS:TH1",
        doc="Bragg Upstream/TH1 Axis",
        kind="normal",
    )

    th2 = Cpt(
        BeckhoffAxis,
        ":MMS:TH2",
        doc="Bragg Downstream/TH2 Axis",
        kind="normal",
    )

    yag_txd = Cpt(
        BeckhoffAxis,
        ":MMS:TXD",
        doc="YAG Diagnostic X Axis",
        kind="normal",
    )

    yag_tyd = Cpt(
        BeckhoffAxis,
        ":MMS:TYD",
        doc="YAG Diagnostic Y Axis",
        kind="normal",
    )

    lightpath_cpts = ["tx_state"]

    def __init__(
        self,
        prefix: str,
        hutch: Optional[str] = None,
        acr_status_suffix: str = "AO805",
        acr_status_pv_index: int = 2,
        **kwargs,
    ):
        # These values must exist before formatted components are created.
        self._initial_hutch = resolve_hutch(prefix, hutch)
        self.acr_status_suffix = acr_status_suffix
        self.acr_status_pv_index = int(acr_status_pv_index)

        super().__init__(prefix, **kwargs)

        self._hutch_sync_lock = threading.RLock()

        self._hutch_signals = (
            self.hutch,
            self.energy_with_vernier.hutch,
            self.energy_with_acr_status.hutch,
        )

        # Initialize all selectors before installing synchronization.
        for signal in self._hutch_signals:
            signal.put(self._initial_hutch)

        for signal in self._hutch_signals:
            signal.subscribe(self._sync_hutch_selection, run=False)

    @property
    def hutch_name(self) -> str:
        """Currently selected beam destination."""
        return self.hutch.selected_name

    def _sync_hutch_selection(self, *, value, **kwargs):
        with self._hutch_sync_lock:
            for signal in self._hutch_signals:
                # Avoid unnecessary writes and recursive update loops.
                if signal.get() != value:
                    signal.put(value)

    def _proxy_method(method_name):
        """Proxy a method from tx_state."""

        def method_selector(self, *args, **kwargs):
            return getattr(self.tx_state, method_name)(*args, **kwargs)

        return method_selector

    def _proxy_property(prop_name):
        """Create a read-only property proxy to tx_state."""

        def getter(self):
            return getattr(self.tx_state, prop_name)

        return property(getter)

    inserted = _proxy_property("inserted")
    check_inserted = _proxy_method("check_inserted")
    removed = _proxy_property("removed")
    check_removed = _proxy_method("check_removed")
    insert = _proxy_method("insert")
    remove = _proxy_method("remove")
