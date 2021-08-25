import logging

import numpy as np
import pytest
from ophyd.sim import fake_device_cache, make_fake_device

import pcdsdevices.ccm as ccm
from pcdsdevices.sim import FastMotor

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


def make_fake_ccm():
    fake_device_cache[ccm.CCMMotor] = FastMotor
    FakeCCM = make_fake_device(ccm.CCM)
    fake_ccm = FakeCCM(alio_prefix='ALIO', theta2fine_prefix='THETA',
                       theta2coarse_prefix='THTA', chi2_prefix='CHI',
                       x_down_prefix='X:DOWN', x_up_prefix='X:UP',
                       y_down_prefix='Y:DOWN', y_up_north_prefix='Y:UP:NORTH',
                       y_up_south_prefix='Y:UP:SOUTH', in_pos=8, out_pos=0,
                       name='fake_ccm')

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

    theta_func = ccm.alio_to_theta(SAMPLE_ALIO, calc.theta0, calc.gr, calc.gd)
    wavelength_func = ccm.theta_to_wavelength(theta_func, calc.dspacing)
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
def test_disconnected_ccm():
    ccm.CCM(alio_prefix='ALIO', theta2fine_prefix='THETA',
            theta2coarse_prefix='THTA', chi2_prefix='CHI',
            x_down_prefix='X:DOWN', x_up_prefix='X:UP',
            y_down_prefix='Y:DOWN', y_up_north_prefix='Y:UP:NORTH',
            y_up_south_prefix='Y:UP:SOUTH', in_pos=8, out_pos=0,
            name='ccm')
