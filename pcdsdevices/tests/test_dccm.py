from unittest.mock import Mock, PropertyMock, call, patch, sentinel

import pytest
from ophyd.sim import make_fake_device

from ..dccm import DCCM, DCCMEnergy, DCCMEnergyWithVernier


@pytest.fixture
def fake_dccm():
    cls = make_fake_device(DCCM)
    return cls(
        "TST:SP1T0",
        hutch="TST2",
        acr_status_suffix="AO804",
        acr_status_pv_index="9",
        name="fake_dccm",
    )


def test_acr_energy_params(fake_dccm):
    vernier = fake_dccm.energy_with_vernier.acr_energy
    acr = fake_dccm.energy_with_acr_status.acr_energy

    assert vernier.prefix == fake_dccm.hutch
    assert acr.prefix == fake_dccm.hutch
    assert acr.acr_status_suffix == fake_dccm.acr_status_suffix
    assert acr.pv_index == fake_dccm.acr_status_pv_index


@pytest.mark.parametrize(
    "component, suffix",
    [
        ("tx_state", ":MMS:STATE"),
        ("th1", ":MMS:TH1"),
        ("th2", ":MMS:TH2"),
        ("tx", ":MMS:TX"),
        ("txd", ":MMS:TXD"),
        ("tyd", ":MMS:TYD"),
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


@pytest.mark.parametrize(
    "component",
    ["crys_01", "crys_02", "energy"],
)
@pytest.mark.parametrize("wait", [True, False])
def test_move_handshake(fake_dccm, monkeypatch, component, wait):
    energy = getattr(fake_dccm, component)
    energy.done.sim_put(0)

    # Simulate the PLC:
    # reset clears Done, and actuate completes the move by setting Done.
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

    if component == "energy":
        energy.axis_coupling_enable.sim_put(0)

    moved_cb = Mock()
    status = energy.move(
        12.5,
        wait=wait,
        timeout=1.0,
        moved_cb=moved_cb,
    )
    status.wait(timeout=1.0)

    assert status.done
    assert status.success
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


def test_move_wait_false_returns_pending_reset_status(fake_dccm, monkeypatch):
    energy = fake_dccm.crys_01
    energy.done.sim_put(0)

    # Leave Done high after the second reset to simulate a delayed PLC
    # acknowledgement. wait=False skips waiting for this final low state.
    monkeypatch.setattr(energy.reset, "put", Mock())
    monkeypatch.setattr(
        energy.actuate,
        "put",
        Mock(side_effect=lambda *args, **kwargs: energy.done.sim_put(1)),
    )

    moved_cb = Mock()
    status = energy.move(
        12.5,
        wait=False,
        timeout=1.0,
        moved_cb=moved_cb,
    )

    try:
        assert not status.done
        moved_cb.assert_not_called()
    finally:
        # Complete the handshake and clean up the subscription.
        energy.done.sim_put(0)
        status.wait(timeout=1.0)

    assert status.success
    moved_cb.assert_called_once_with(obj=energy)


@pytest.mark.parametrize(
    "component",
    ["energy_with_vernier", "energy_with_acr_status"],
)
def test_vernier_move_requests_ev(fake_dccm, monkeypatch, component):
    energy = getattr(fake_dccm, component)
    request_put = Mock()
    monkeypatch.setattr(energy.acr_energy, "put", request_put)

    moved_cb = Mock()

    with patch.object(
        DCCMEnergy,
        "move",
        autospec=True,
        return_value=sentinel.move_status,
    ) as parent_move:
        calls = Mock()
        calls.attach_mock(request_put, "request")
        calls.attach_mock(parent_move, "move")

        status = energy.move(
            12.5,
            wait=False,
            timeout=2.0,
            moved_cb=moved_cb,
        )

        # The ACR request uses eV; the DCCM move uses keV.
        assert calls.mock_calls == [
            call.request(12500.0),
            call.move(energy, 12.5, False, 2.0, moved_cb),
        ]

    assert status is sentinel.move_status


@pytest.mark.parametrize(
    "prefix, hutch, expected",
    [
        ("TXI:DCCM", None, "TXI"),
        ("CXI:DCCM", None, "CXI"),
        ("MEC:DCCM", None, "MEC"),
        ("MFX:DCCM", None, "MFX"),
        ("XCS:DCCM", None, "XCS"),
        ("UNKNOWN:DCCM", None, "TST"),
        ("TXI:DCCM", "TST2", "TST2"),
    ],
)
def test_vernier_hutch_selection(prefix, hutch, expected):
    cls = make_fake_device(DCCMEnergyWithVernier)
    energy = cls(prefix, hutch=hutch, name="energy")

    assert energy.hutch == expected
    assert energy.acr_energy.prefix == expected


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
