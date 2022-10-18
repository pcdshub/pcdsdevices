import logging
import time

import numpy as np
import pytest
from ophyd.sim import fake_device_cache, make_fake_device

from .. import ccm
from ..sim import FastMotor

logger = logging.getLogger(__name__)


SAMPLE_ALIO = 4.575  # Current value as of writing this file
SAMPLE_THETA = 1.2  # Modest angle
SAMPLE_WAVELENGTH = 1.5  # hard xray


# Make sure the calcs are properly inverted
def test_theta_alio_inversion():
    logger.debug('test_theta_alio_inversion')
    theta = ccm.alio_to_theta(SAMPLE_ALIO, ccm.default_theta0, ccm.default_gr,
                              ccm.default_gd)
    alio_calc = ccm.theta_to_alio(theta, ccm.default_theta0, ccm.default_gr,
                                  ccm.default_gd)
    # Unlike the other inversions, this is just an approximation
    assert np.isclose(alio_calc, SAMPLE_ALIO)


def test_wavelength_theta_inversion():
    logger.debug('test_wavelength_theta_inversion')
    wavelength = ccm.theta_to_wavelength(SAMPLE_THETA, ccm.default_dspacing)
    theta = ccm.wavelength_to_theta(wavelength, ccm.default_dspacing)
    logger.debug('%s, %s', wavelength, theta)
    assert np.isclose(theta, SAMPLE_THETA)
    theta = ccm.wavelength_to_theta(SAMPLE_WAVELENGTH, ccm.default_dspacing)
    wavelength = ccm.theta_to_wavelength(theta, ccm.default_dspacing)
    logger.debug('%s, %s', wavelength, theta)
    assert np.isclose(wavelength, SAMPLE_WAVELENGTH)


def test_energy_wavelength_inversion():
    logger.debug('test_energy_wavelength_inversion')
    energy = ccm.wavelength_to_energy(SAMPLE_WAVELENGTH)
    wavelength_calc = ccm.energy_to_wavelength(energy)
    assert wavelength_calc == SAMPLE_WAVELENGTH


@pytest.fixture(scope='function')
def fake_ccm():
    return make_fake_ccm()


class FakeAlio(FastMotor):
    home = None

    def kill(self):
        print('Killing alio PID')


def make_fake_ccm():
    fake_device_cache[ccm.CCMMotor] = FastMotor
    fake_device_cache[ccm.CCMAlio] = FakeAlio
    FakeCCM = make_fake_device(ccm.CCM)
    fake_ccm = FakeCCM(alio_prefix='ALIO', theta2fine_prefix='THETA',
                       theta2coarse_prefix='THTA', chi2_prefix='CHI',
                       x_down_prefix='X:DOWN', x_up_prefix='X:UP',
                       y_down_prefix='Y:DOWN', y_up_north_prefix='Y:UP:NORTH',
                       y_up_south_prefix='Y:UP:SOUTH', in_pos=8, out_pos=0,
                       name='fake_ccm',
                       input_branches=['X0'], output_branches=['X0'])

    def init_pos(mot, pos=0):
        mot.user_readback.sim_put(0)
        mot.user_setpoint.sim_put(0)
        mot.user_setpoint.sim_set_limits((0, 0))
        mot.motor_spg.sim_put(2)
        mot.part_number.sim_put('tasdf')

    init_pos(fake_ccm.x.down)
    init_pos(fake_ccm.x.up)
    init_pos(fake_ccm.y.down)
    init_pos(fake_ccm.y.up_north)
    init_pos(fake_ccm.y.up_south)

    fake_ccm.alio.set(SAMPLE_ALIO)
    fake_ccm.energy.alio.set(SAMPLE_ALIO)
    fake_ccm.energy_with_vernier.alio.set(SAMPLE_ALIO)
    fake_ccm.energy_with_vernier.vernier.setpoint.sim_put(0)

    return fake_ccm


def test_fake_ccm(fake_ccm):
    logger.debug('test_fake_ccm')
    fake_ccm.get()


# Make sure we set up the forward/inverse to use the right methods
def test_ccm_calc(fake_ccm):
    logger.debug('test_ccm_calc')
    calc = fake_ccm.energy

    logger.debug('physics pos is %s', calc.position)
    logger.debug('real pos is %s', calc.real_position)
    logger.debug('sample alio is %s', SAMPLE_ALIO)

    theta_func = ccm.alio_to_theta(
        SAMPLE_ALIO,
        calc.theta0_rad_val,
        calc.gr_val,
        calc.gd_val,
    )
    wavelength_func = ccm.theta_to_wavelength(theta_func, calc.dspacing_val)
    energy_func = ccm.wavelength_to_energy(wavelength_func)
    energy = calc.energy.position
    assert energy == energy_func

    calc.alio.move(0)
    calc.move(energy, wait=False)
    assert np.isclose(calc.alio.position, SAMPLE_ALIO)

    calc.alio.move(calc.alio.position)
    calc.move(energy=calc.energy.position, wait=False)
    assert np.isclose(calc.alio.position, SAMPLE_ALIO)


# Make sure sync'd axes work and that unk/in/out states work
@pytest.mark.timeout(5)
def test_ccm_main(fake_ccm):
    logger.debug('test_ccm_main')
    fake_ccm.y.move(5, wait=False)
    assert fake_ccm.y.down.user_setpoint.get() == 5
    assert fake_ccm.y.up_north.user_setpoint.get() == 5
    assert fake_ccm.y.up_south.user_setpoint.get() == 5

    assert fake_ccm.removed
    assert not fake_ccm.inserted

    fake_ccm.x.down.user_readback.sim_put(8)
    fake_ccm.x.up.user_readback.sim_put(8)
    assert not fake_ccm.removed
    assert fake_ccm.inserted

    fake_ccm.x.down.user_readback.sim_put(4)
    fake_ccm.x.up.user_readback.sim_put(4)
    assert not fake_ccm.removed
    assert not fake_ccm.inserted

    fake_ccm.insert(wait=False)
    assert fake_ccm.x.down.user_setpoint.get() == 8
    assert fake_ccm.x.up.user_setpoint.get() == 8

    fake_ccm.remove(wait=False)
    assert fake_ccm.x.down.user_setpoint.get() == 0
    assert fake_ccm.x.up.user_setpoint.get() == 0


@pytest.mark.timeout(5)
def test_vernier(fake_ccm):
    logger.debug('test_vernier')

    pseudopos = fake_ccm.energy_with_vernier

    # Moving with vernier should move the energy request motor too
    pseudopos.move(7, wait=False)
    assert np.isclose(pseudopos.energy.position, 7)
    assert pseudopos.vernier.position == 7000

    pseudopos.move(8, wait=False)
    assert np.isclose(pseudopos.energy.position, 8)
    assert pseudopos.vernier.position == 8000

    pseudopos.move(9, wait=False)
    assert np.isclose(pseudopos.energy.position, 9)
    assert pseudopos.vernier.position == 9000

    # Small moves (less than 30eV) should be skipped on the energy request
    pseudopos.move(9.001, wait=False)
    assert np.isclose(pseudopos.energy.position, 9.001)
    assert pseudopos.vernier.position == 9000

    # Unless we set the option for not skipping them
    pseudopos.vernier.skip_small_moves = False
    pseudopos.move(9.002, wait=False)
    assert np.isclose(pseudopos.energy.position, 9.002)
    assert pseudopos.vernier.position == 9002


@pytest.mark.timeout(5)
def test_set_current_position(fake_ccm):
    logger.debug('test_set_current_position')
    mot = fake_ccm.energy.energy
    for energy in range(6, 14):
        mot.set_current_position(energy)
        assert np.isclose(mot.position, energy)


@pytest.mark.timeout(5)
def test_check_valid_constant(fake_ccm):
    logger.debug('test_check_valid_constant')

    # First call to make_valid sends the first monitor update
    def make_valid(sig, valid):
        if valid:
            sig.put(1)
        else:
            sig.put(0)

    def make_conn(sig, conn):
        sig._metadata['connected'] = conn

    def output(sig):
        return fake_ccm._check_valid_constant(sig, sig.get())

    test_sig = fake_ccm.dspacing

    # Can we get to all the enum values?
    make_conn(test_sig, False)
    assert output(test_sig) == ccm.CCMConstantWarning.ALWAYS_DISCONNECT
    make_conn(test_sig, True)
    make_valid(test_sig, False)
    assert output(test_sig) == ccm.CCMConstantWarning.INVALID_CONNECT
    make_conn(test_sig, False)
    assert output(test_sig) == ccm.CCMConstantWarning.INVALID_DISCONNECT
    make_conn(test_sig, True)
    make_valid(test_sig, True)
    assert output(test_sig) == ccm.CCMConstantWarning.NO_WARNING
    make_conn(test_sig, False)
    assert output(test_sig) == ccm.CCMConstantWarning.VALID_DISCONNECT

    # theta0_deg is allowed to be zero, unlike the others
    test_sig2 = fake_ccm.theta0_deg
    make_conn(test_sig2, True)
    make_valid(test_sig2, False)
    assert output(test_sig2) == ccm.CCMConstantWarning.NO_WARNING


@pytest.mark.timeout(5)
def test_show_constant_warning(fake_ccm, caplog):
    logger.debug('test_show_constant_warning')
    for warning in (
        ccm.CCMConstantWarning.NO_WARNING,
        ccm.CCMConstantWarning.ALWAYS_DISCONNECT,
        ccm.CCMConstantWarning.VALID_DISCONNECT,
        ccm.CCMConstantWarning.INVALID_DISCONNECT,
        ccm.CCMConstantWarning.INVALID_CONNECT,
    ):
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            fake_ccm._show_constant_warning(
                warning,
                fake_ccm.dspacing,
                0.111111,
                0.222222,
            )
        if warning == ccm.CCMConstantWarning.NO_WARNING:
            assert len(caplog.records) == 0
        else:
            assert len(caplog.records) == 1


@pytest.mark.timeout(5)
def test_warn_invalid_constants(fake_ccm, caplog):
    logger.debug('test_warn_invalid_constants')
    # Trick the warning into thinking we've be initialized for a while
    fake_ccm._init_time = time.monotonic() - 1000
    fake_ccm.theta0_deg.put(0)
    fake_ccm.dspacing.put(0)
    fake_ccm.gr.put(0)
    fake_ccm.gd.put(0)
    # We expect three warnings from the fake PVs that start at 0
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        fake_ccm.warn_invalid_constants(only_new=False)
        assert len(caplog.records) == 3
        # We expect the warnings to not repeat
        caplog.clear()
        fake_ccm.warn_invalid_constants(only_new=True)
        assert len(caplog.records) == 0
        # Unless we ask them to
        caplog.clear()
        fake_ccm.warn_invalid_constants(only_new=False)
        assert len(caplog.records) == 3
        # Let's fix the issue and make sure no warnings are shown
        fake_ccm.reset_calc_constant_defaults(confirm=False)
        caplog.clear()
        fake_ccm.warn_invalid_constants(only_new=False)
        assert len(caplog.records) == 0


@pytest.mark.timeout(5)
def test_disconnected_ccm():
    ccm.CCM(alio_prefix='ALIO', theta2fine_prefix='THETA',
            theta2coarse_prefix='THTA', chi2_prefix='CHI',
            x_down_prefix='X:DOWN', x_up_prefix='X:UP',
            y_down_prefix='Y:DOWN', y_up_north_prefix='Y:UP:NORTH',
            y_up_south_prefix='Y:UP:SOUTH', in_pos=8, out_pos=0,
            name='ccm')
