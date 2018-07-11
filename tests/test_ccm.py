import logging

import numpy as np
from ophyd.sim import make_fake_device
import pytest

import pcdsdevices.ccm as ccm

logger = logging.getLogger(__name__)


SAMPLE_ALIO = 4.575  # Current value as of writing this file
SAMPLE_THETA = 1.2  # Modest angle
SAMPLE_WAVELENGTH = 10  # xray


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
    wavelength = ccm.wavelength_to_theta(SAMPLE_THETA, ccm.default_dspacing)
    theta_calc = ccm.theta_to_wavelength(wavelength, ccm.default_dspacing)
    assert theta_calc == SAMPLE_THETA


def test_energy_wavelength_inversion():
    logger.debug('test_energy_wavelength_inversion')
    energy = ccm.wavelength_to_energy(SAMPLE_WAVELENGTH)
    wavelength_calc = ccm.energy_to_wavelength(energy)
    assert wavelength_calc == SAMPLE_WAVELENGTH


@pytest.fixture(scope='function')
def fake_ccm():
    FakeCCM = make_fake_device(ccm.CCM)
    fake_ccm = FakeCCM(x_down='X:DOWN', x_up='X:UP', y_down='Y:DOWN',
                       y_up_north='Y:UP:NORTH', y_up_south='Y:UP:SOUTH',
                       alio='ALIO', theta2fine='THETA', inpos=8, outpos=0,
                       name='fake_ccm')
    fake_ccm.calc.alio.readback.sim_put(SAMPLE_ALIO)
    fake_ccm.calc.alio.setpoint.sim_put(SAMPLE_ALIO)
    fake_ccm.x.down.user_readback.sim_put(0)
    fake_ccm.x.up.user_readback.sim_put(0)
    fake_ccm.x.down.user_setpoint.sim_put(0)
    fake_ccm.x.up.user_setpoint.sim_put(0)
    fake_ccm.y.down.user_setpoint.sim_put(0)
    fake_ccm.y.up_north.user_setpoint.sim_put(0)
    fake_ccm.y.up_south.user_setpoint.sim_put(0)


# Make sure we set up the forward/inverse to use the right methods
def test_ccm_calc(fake_ccm):
    logger.debug('test_ccm_calc')
    calc = fake_ccm.calc

    theta = calc.theta.position
    theta_func = ccm.alio_to_theta(SAMPLE_ALIO, calc.theta0, calc.gr, calc.gd)
    assert theta == theta_func

    wavelength = calc.wavelength.position
    wavelength_func = ccm.theta_to_wavelength(theta, calc.dspacing)
    assert wavelength == wavelength_func

    energy = calc.energy.position
    energy_func = ccm.wavelength_to_energy(energy)
    assert energy == energy_func

    calc.alio.readback.sim_put(0)
    calc.alio.setpoint.sim_put(0)
    calc.move(energy, wait=True)

    assert calc.alio.setpoint.get() == SAMPLE_ALIO


# Make sure sync'd axes work and that unk/in/out states work
def test_ccm_main(fake_ccm):
    fake_ccm.y.move(5)
    assert fake_ccm.y.down.user_setpoint.get() == 5
    assert fake_ccm.y.up_north.user_setpoint.get() == 5
    assert fake_ccm.y.up_south.user_setpoint.get() == 5

    assert fake_ccm.position == 'OUT'
    assert fake_ccm.removed
    assert not fake_ccm.inserted

    fake_ccm.x.down.user_readback.sim_put(8)
    fake_ccm.x.up.user_readback.sim_put(8)
    assert fake_ccm.position == 'IN'
    assert not fake_ccm.removed
    assert fake_ccm.inserted

    fake_ccm.x.down.user_readback.sim_put(4)
    fake_ccm.x.up.user_readback.sim_put(4)
    assert fake_ccm.position == 'Unknown'
    assert not fake_ccm.removed
    assert not fake_ccm.inserted

    fake_ccm.insert()
    assert fake_ccm.x.down.user_setpoint.get() == 8
    assert fake_ccm.x.up.user_setpoint.get() == 8

    fake_ccm.remove()
    assert fake_ccm.x.down.user_setpoint.get() == 0
    assert fake_ccm.x.up.user_setpoint.get() == 0
