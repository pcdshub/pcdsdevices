from unittest.mock import Mock, PropertyMock, call, patch, sentinel

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import Status

from ..dccm import (
    DCCM,
    DCCMCrystal,
    DCCMEnergy,
    DCCMEnergyWithVernier,
    HutchSelectionSignal,
    resolve_hutch,
)

HUTCH_NAMES = ("L", "XCS", "CXI", "MEC", "MFX", "XPP")
ACR_HUTCH_NAMES = ("XCS", "CXI", "MEC", "MFX", "XPP")
ACR_COMPONENTS = ("energy_with_vernier", "energy_with_acr_status")


@pytest.fixture
def fake_dccm():
    cls = make_fake_device(DCCM)
    return cls(
        "TST:SP1T0",
        hutch="XPP",
        acr_status_suffix="AO804",
        acr_status_pv_index="9",
        name="fake_dccm",
    )


def configure_plc_handshake(energy, monkeypatch):
    """Simulate a complete Done-high/reset/Done-low handshake."""
    energy.error.sim_put(0)
    energy.done.sim_put(0)

    reset_put = Mock(side_effect=lambda *args, **kwargs: energy.done.sim_put(0))
    setpoint_put = Mock(wraps=energy.setpoint.put)
    actuate_put = Mock(side_effect=lambda *args, **kwargs: energy.done.sim_put(1))

    monkeypatch.setattr(energy.reset, "put", reset_put)
    monkeypatch.setattr(energy.setpoint, "put", setpoint_put)
    monkeypatch.setattr(energy.actuate, "put", actuate_put)

    commands = Mock()
    commands.attach_mock(reset_put, "reset")
    commands.attach_mock(setpoint_put, "setpoint")
    commands.attach_mock(actuate_put, "actuate")
    return commands


@pytest.mark.parametrize(
    "prefix, hutch, expected",
    [
        ("L:DCCM", None, "L"),
        ("XCS:DCCM", None, "XCS"),
        ("CXI:DCCM", None, "CXI"),
        ("MEC:DCCM", None, "MEC"),
        ("MFX:DCCM", None, "MFX"),
        ("XPP:DCCM", None, "XPP"),
        (":tst:cxi:dccm:", None, "CXI"),
        ("CXI:DCCM", "", "CXI"),
        ("CXI:DCCM", "   ", "CXI"),
        ("UNKNOWN:DCCM", " xpp ", "XPP"),
        ("CXI:DCCM", "MEC", "MEC"),
    ],
)
def test_resolve_hutch(prefix, hutch, expected):
    assert resolve_hutch(prefix, hutch) == expected


@pytest.mark.parametrize(
    "prefix, hutch",
    [
        ("UNKNOWN:DCCM", None),
        ("TXI:DCCM", None),
        ("NOTCXI:DCCM", None),
        ("", None),
        ("CXI:DCCM", "TST2"),
        ("CXI:DCCM", "TXI"),
    ],
)
def test_resolve_hutch_invalid(prefix, hutch):
    with pytest.raises(ValueError):
        resolve_hutch(prefix, hutch)


def test_hutch_signal_metadata():
    signal = HutchSelectionSignal(name="hutch")

    assert signal.get() == 0
    assert signal.selected_name == "L"
    assert tuple(signal.enum_strs) == HUTCH_NAMES
    assert tuple(signal.metadata["enum_strs"]) == HUTCH_NAMES
    assert tuple(signal.describe()["hutch"]["enum_strs"]) == HUTCH_NAMES


@pytest.mark.parametrize("index, name", enumerate(HUTCH_NAMES))
def test_hutch_signal_accepts_names_and_indices(index, name):
    signal = HutchSelectionSignal(name="hutch")

    signal.put(f" {name.lower()} ")
    assert signal.get() == index
    assert signal.selected_name == name

    signal.put(index)
    assert signal.get() == index
    assert signal.selected_name == name


@pytest.mark.parametrize(
    "value",
    [-1, len(HUTCH_NAMES), 1.5, None, "", "TST2", "1"],
)
def test_hutch_signal_rejects_invalid_values(value):
    signal = HutchSelectionSignal(name="hutch", value="CXI")

    with pytest.raises(ValueError):
        signal.put(value)

    assert signal.selected_name == "CXI"


@pytest.mark.parametrize(
    "prefix, hutch, expected",
    [
        ("XCS:DCCM", None, "XCS"),
        ("CXI:DCCM", None, "CXI"),
        ("MEC:DCCM", None, "MEC"),
        ("MFX:DCCM", None, "MFX"),
        ("XPP:DCCM", None, "XPP"),
        ("UNKNOWN:DCCM", " xpp ", "XPP"),
        ("CXI:DCCM", "MEC", "MEC"),
    ],
)
def test_vernier_hutch_selection(prefix, hutch, expected):
    cls = make_fake_device(DCCMEnergyWithVernier)
    energy = cls(prefix, hutch=hutch, name="energy")

    assert energy.hutch_name == expected
    assert energy.hutch.get() == HUTCH_NAMES.index(expected)
    assert energy.acr_energy.prefix == expected


@pytest.mark.parametrize(
    "prefix, hutch",
    [
        ("UNKNOWN:DCCM", None),
        ("TXI:DCCM", None),
        ("CXI:DCCM", "TST2"),
    ],
)
def test_vernier_invalid_hutch(prefix, hutch):
    cls = make_fake_device(DCCMEnergyWithVernier)

    with pytest.raises(ValueError):
        cls(prefix, hutch=hutch, name="energy")


@pytest.mark.parametrize(
    "source",
    ["assembly", "energy_with_vernier", "energy_with_acr_status"],
)
def test_hutch_selection_synchronization(fake_dccm, source):
    if source == "assembly":
        signal = fake_dccm.hutch
    else:
        signal = getattr(fake_dccm, source).hutch

    for name in HUTCH_NAMES:
        signal.put(name)

        assert fake_dccm.hutch_name == name
        for component in ACR_COMPONENTS:
            energy = getattr(fake_dccm, component)
            assert energy.hutch_name == name
            assert energy.hutch.get() == fake_dccm.hutch.get()


def test_acr_energy_params(fake_dccm):
    vernier = fake_dccm.energy_with_vernier
    acr = fake_dccm.energy_with_acr_status

    assert vernier.acr_energy.prefix == "XPP"
    assert acr.acr_energy.prefix == "XPP"

    assert acr.acr_status_suffix == "AO804"
    assert acr.pv_index == 9
    assert acr.acr_requests.acr_status_suffix == "AO804"
    assert acr.acr_requests.pv_index == 9


@pytest.mark.parametrize("component", ACR_COMPONENTS)
def test_acr_request_devices_are_reused(fake_dccm, component):
    energy = getattr(fake_dccm, component)

    energy.hutch.put("CXI")
    cxi_request = energy.acr_energy

    energy.hutch.put("MEC")
    mec_request = energy.acr_energy

    assert mec_request is not cxi_request
    assert cxi_request.prefix == "CXI"
    assert mec_request.prefix == "MEC"

    energy.hutch.put("CXI")
    assert energy.acr_energy is cxi_request


def test_acr_requests_reject_invalid_hutch(fake_dccm):
    with pytest.raises(ValueError):
        fake_dccm.energy_with_vernier.acr_requests.for_hutch("TST2")


@pytest.mark.parametrize(
    "component, suffix",
    [
        ("tx_state", ":MMS:STATE"),
        ("th1", ":MMS:TH1"),
        ("th2", ":MMS:TH2"),
        ("tx", ":MMS:TX"),
        ("yag_txd", ":MMS:TXD"),
        ("yag_tyd", ":MMS:TYD"),
        ("crys_01", ":CTC:CRYS:01"),
        ("crys_02", ":CTC:CRYS:02"),
        ("energy", ":CTC:CRYS:01"),
        ("energy_with_vernier", ":CTC:CRYS:01"),
        ("energy_with_acr_status", ":CTC:CRYS:01"),
    ],
)
def test_component_prefixes(fake_dccm, component, suffix):
    assert getattr(fake_dccm, component).prefix == fake_dccm.prefix + suffix


@pytest.mark.parametrize("prefix", ["TST:DCCM", "TST:DCCM:"])
@pytest.mark.parametrize("crystal", ["01", "02", 2])
def test_energy_crystal_prefix(prefix, crystal):
    cls = make_fake_device(DCCMEnergy)
    energy = cls(prefix, crystal=crystal, name="energy")

    assert energy.crystal == int(crystal)
    assert energy._base_prefix == "TST:DCCM"
    assert energy.prefix == f"TST:DCCM:CTC:CRYS:{int(crystal):02d}"


def test_axis_coupling(fake_dccm):
    energy = fake_dccm.energy

    energy.axis_coupling_enable.sim_put(0)
    energy.couple_axis()
    assert energy.axis_coupling_enable.get() == 1

    energy.decouple_axis()
    assert energy.axis_coupling_enable.get() == 0


@pytest.mark.parametrize("component", ["crys_01", "crys_02", "energy"])
def test_energy_limits(fake_dccm, component):
    energy = getattr(fake_dccm, component)

    assert energy.limits == fake_dccm.energy_limits
    assert energy.low_limit_travel.get() == fake_dccm.energy_limits[0]
    assert energy.high_limit_travel.get() == fake_dccm.energy_limits[1]


@pytest.mark.parametrize(
    "position",
    [None, "invalid", float("nan"), float("inf"), -float("inf")],
)
def test_invalid_energy(fake_dccm, position):
    with pytest.raises(ValueError):
        fake_dccm.crys_01.check_value(position)


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_move_timeout(fake_dccm, timeout):
    with pytest.raises(ValueError, match="positive finite"):
        fake_dccm.crys_01.move(12.5, wait=False, timeout=timeout)


@pytest.mark.parametrize("component", ["crys_01", "crys_02", "energy"])
@pytest.mark.parametrize("wait", [True, False])
def test_move_handshake(fake_dccm, monkeypatch, component, wait):
    energy = getattr(fake_dccm, component)
    commands = configure_plc_handshake(energy, monkeypatch)

    if component == "energy":
        energy.axis_coupling_enable.sim_put(0)

    moved_cb = Mock()
    status = energy.move(
        12.5,
        wait=wait,
        timeout=2.0,
        moved_cb=moved_cb,
    )
    status.wait(timeout=2.0)

    assert status.done
    assert status.success
    assert not energy.moving
    assert energy.setpoint.get() == 12.5
    assert energy.done.get() == 0
    assert commands.mock_calls == [
        call.reset(1, wait=True),
        call.setpoint(12.5, wait=True),
        call.actuate(1, wait=True),
        call.reset(1, wait=True),
    ]
    moved_cb.assert_called_once_with(obj=energy)

    if component == "energy":
        assert energy.axis_coupling_enable.get() == 1


def test_move_wait_false_returns_pending_status(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.error.sim_put(0)
    energy.done.sim_put(0)

    # Accept the commands without simulating PLC completion.
    monkeypatch.setattr(energy.reset, "put", Mock())
    monkeypatch.setattr(energy.setpoint, "put", Mock())
    monkeypatch.setattr(energy.actuate, "put", Mock())
    monkeypatch.setattr(energy.stop_signal, "put", Mock())

    status = energy.move(12.5, wait=False, timeout=10.0)

    try:
        assert not status.done
        energy.setpoint.put.assert_called_once_with(12.5, wait=True)
        energy.actuate.put.assert_called_once_with(1, wait=True)
    finally:
        # Finish the status and clean up handshake subscriptions.
        energy.stop(success=True)
        status.wait(timeout=2.0)


def test_move_rejects_overlapping_moves(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.error.sim_put(0)

    # Represent an existing move without starting a real handshake.
    active_status = Mock()
    active_status.done = False
    monkeypatch.setattr(energy, "_active_move_status", active_status)

    actuate_put = Mock()
    monkeypatch.setattr(energy.actuate, "put", actuate_put)

    with pytest.raises(RuntimeError, match="already has an active move"):
        energy.move(13.0, wait=False, timeout=2.0)

    actuate_put.assert_not_called()


def test_move_rejects_existing_plc_error(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.error_msg.sim_put("PLC fault")
    energy.error.sim_put(1)
    actuate_put = Mock()
    monkeypatch.setattr(energy.actuate, "put", actuate_put)

    with pytest.raises(RuntimeError, match="PLC fault"):
        energy.move(12.5, wait=False)

    actuate_put.assert_not_called()
    assert not energy.moving


def test_move_fails_on_plc_error(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.error.sim_put(0)
    energy.done.sim_put(0)
    monkeypatch.setattr(energy.reset, "put", Mock())
    monkeypatch.setattr(energy.actuate, "put", Mock())

    status = energy.move(12.5, wait=False, timeout=2.0)

    energy.error_msg.sim_put("Motion fault")
    energy.error.sim_put(1)

    with pytest.raises(RuntimeError, match="Motion fault"):
        status.wait(timeout=2.0)

    assert status.done
    assert not status.success
    assert not energy.moving


def test_move_command_failure(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.error.sim_put(0)
    energy.done.sim_put(0)
    monkeypatch.setattr(energy.reset, "put", Mock())
    monkeypatch.setattr(
        energy.setpoint,
        "put",
        Mock(side_effect=RuntimeError("Setpoint write failed")),
    )

    status = energy.move(12.5, wait=False, timeout=2.0)

    with pytest.raises(RuntimeError, match="Setpoint write failed"):
        status.wait(timeout=2.0)

    assert not status.success
    assert not energy.moving


@pytest.mark.parametrize("success", [True, False])
def test_stop_active_move(fake_dccm, monkeypatch, success):
    energy = fake_dccm.crys_01
    energy.error.sim_put(0)
    energy.done.sim_put(0)
    monkeypatch.setattr(energy.reset, "put", Mock())
    monkeypatch.setattr(energy.actuate, "put", Mock())
    stop_put = Mock()
    monkeypatch.setattr(energy.stop_signal, "put", stop_put)

    status = energy.move(12.5, wait=False, timeout=2.0)
    energy.stop(success=success)

    stop_put.assert_called_once_with(1, wait=True)

    if success:
        status.wait(timeout=2.0)
    else:
        with pytest.raises(RuntimeError, match="move stopped"):
            status.wait(timeout=2.0)

    assert status.done
    assert status.success is success
    assert not energy.moving


@pytest.mark.parametrize("component", ACR_COMPONENTS)
def test_vernier_move_requests_ev(fake_dccm, monkeypatch, component):
    energy = getattr(fake_dccm, component)
    energy.error.sim_put(0)
    energy.axis_coupling_enable.sim_put(0)

    acr_status = Status()
    dccm_status = Status()
    request_move = Mock(return_value=acr_status)
    monkeypatch.setattr(energy.acr_energy, "move", request_move)

    moved_cb = Mock()

    with patch.object(
        DCCMCrystal,
        "move",
        autospec=True,
        return_value=dccm_status,
    ) as crystal_move:
        calls = Mock()
        calls.attach_mock(request_move, "request")
        calls.attach_mock(crystal_move, "move")

        status = energy.move(
            12.5,
            wait=False,
            timeout=2.0,
            moved_cb=moved_cb,
        )

        assert calls.mock_calls == [
            call.request(12500.0, wait=False, timeout=2.0),
            call.move(
                energy,
                12.5,
                wait=False,
                timeout=2.0,
                moved_cb=None,
            ),
        ]

    assert energy.axis_coupling_enable.get() == 1
    assert not status.done
    moved_cb.assert_not_called()

    acr_status.set_finished()
    assert not status.done
    moved_cb.assert_not_called()

    dccm_status.set_finished()
    status.wait(timeout=2.0)

    assert status.success
    moved_cb.assert_called_once_with(obj=energy)


@pytest.mark.parametrize("component", ACR_COMPONENTS)
@pytest.mark.parametrize("first", ["acr", "dccm"])
def test_vernier_status_requires_both_moves(fake_dccm, monkeypatch, component, first):
    energy = getattr(fake_dccm, component)
    energy.error.sim_put(0)

    acr_status = Status()
    dccm_status = Status()
    monkeypatch.setattr(
        energy.acr_energy,
        "move",
        Mock(return_value=acr_status),
    )

    with patch.object(DCCMCrystal, "move", return_value=dccm_status):
        status = energy.move(12.5, wait=False, timeout=2.0)

    first_status, second_status = (acr_status, dccm_status) if first == "acr" else (dccm_status, acr_status)

    first_status.set_finished()
    assert not status.done

    second_status.set_finished()
    status.wait(timeout=2.0)
    assert status.success


@pytest.mark.parametrize("component", ACR_COMPONENTS)
def test_vernier_move_wait_true(fake_dccm, monkeypatch, component):
    energy = getattr(fake_dccm, component)
    configure_plc_handshake(energy, monkeypatch)

    acr_status = Status()
    acr_status.set_finished()
    request_move = Mock(return_value=acr_status)
    monkeypatch.setattr(energy.acr_energy, "move", request_move)

    status = energy.move(12.5, wait=True, timeout=2.0)

    assert status.done
    assert status.success
    request_move.assert_called_once_with(
        12500.0,
        wait=False,
        timeout=2.0,
    )


@pytest.mark.parametrize("component", ACR_COMPONENTS)
def test_vernier_selection_does_not_retarget_active_request(fake_dccm, monkeypatch, component):
    energy = getattr(fake_dccm, component)
    energy.error.sim_put(0)

    energy.hutch.put("CXI")
    cxi_request = energy.acr_energy
    energy.hutch.put("MEC")
    mec_request = energy.acr_energy
    energy.hutch.put("CXI")

    acr_status = Status()
    dccm_status = Status()
    cxi_move = Mock(return_value=acr_status)
    mec_move = Mock()
    monkeypatch.setattr(cxi_request, "move", cxi_move)
    monkeypatch.setattr(mec_request, "move", mec_move)

    with patch.object(DCCMCrystal, "move", return_value=dccm_status):
        status = energy.move(12.5, wait=False, timeout=2.0)

    energy.hutch.put("MEC")

    assert energy.acr_energy is mec_request
    cxi_move.assert_called_once_with(
        12500.0,
        wait=False,
        timeout=2.0,
    )
    mec_move.assert_not_called()

    acr_status.set_finished()
    dccm_status.set_finished()
    status.wait(timeout=2.0)
    assert status.success


@pytest.mark.parametrize("component", ACR_COMPONENTS)
def test_vernier_dccm_start_failure(fake_dccm, monkeypatch, component):
    energy = getattr(fake_dccm, component)
    energy.error.sim_put(0)

    acr_status = Status()
    acr_status.set_finished()
    request_move = Mock(return_value=acr_status)
    monkeypatch.setattr(energy.acr_energy, "move", request_move)

    cause = RuntimeError("DCCM unavailable")
    with patch.object(DCCMCrystal, "move", side_effect=cause):
        with pytest.raises(
            RuntimeError,
            match="DCCM move failed to start after the ACR energy request",
        ) as exc_info:
            energy.move(12.5, wait=False, timeout=2.0)

    assert exc_info.value.__cause__ is cause
    request_move.assert_called_once_with(
        12500.0,
        wait=False,
        timeout=2.0,
    )


@pytest.mark.parametrize(
    "method_name, args, kwargs",
    [
        ("insert", (), {"wait": False, "timeout": 1.0}),
        ("remove", (), {"wait": False, "timeout": 1.0}),
        ("check_inserted", (), {}),
        ("check_removed", (), {}),
    ],
)
def test_state_method_proxies(fake_dccm, monkeypatch, method_name, args, kwargs):
    method = Mock(return_value=sentinel.result)
    monkeypatch.setattr(fake_dccm.tx_state, method_name, method)

    result = getattr(fake_dccm, method_name)(*args, **kwargs)

    assert result is sentinel.result
    method.assert_called_once_with(*args, **kwargs)


@pytest.mark.parametrize("property_name", ["inserted", "removed"])
@pytest.mark.parametrize("value", [True, False])
def test_state_property_proxies(fake_dccm, property_name, value):
    with patch.object(
        type(fake_dccm.tx_state),
        property_name,
        new_callable=PropertyMock,
        return_value=value,
    ) as state_property:
        assert getattr(fake_dccm, property_name) is value
        state_property.assert_called_once_with()
