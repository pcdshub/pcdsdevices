import logging

import numpy as np

import pcdsdevices.ccm as ccm
from pcdsdevices.sim.pv import using_fake_epics_pv

logger = logging.getLogger(__name__)


SAMPLE_ALIO = 4.575  # Current value as of writing this file
SAMPLE_THETA = 1.2  # Modest angle
SAMPLE_WAVELENGTH = 10  # xray


# Make sure the calcs are properly inverted
def test_theta_alio_inversion():
    logger.debug('test_theta_alio_inversion')
    theta = ccm.alio_to_theta(SAMPLE_ALIO, ccm.gTheta0, ccm.gR, ccm.gD)
    alio_calc = ccm.theta_to_alio(theta, ccm.gTheta0, ccm.gR, ccm.gD)
    # Unlike the other inversions, this is just an approximation
    assert np.isclose(alio_calc, SAMPLE_ALIO)


def test_wavelength_theta_inversion():
    logger.debug('test_wavelength_theta_inversion')
    wavelength = ccm.wavelength_to_theta(SAMPLE_THETA, ccm.gdspacing)
    theta_calc = ccm.theta_to_wavelength(wavelength, ccm.gdspacing)
    assert theta_calc == SAMPLE_THETA


def test_energy_wavelength_inversion():
    logger.debug('test_energy_wavelength_inversion')
    energy = ccm.wavelength_to_energy(SAMPLE_WAVELENGTH)
    wavelength_calc = ccm.energy_to_wavelength(energy)
    assert wavelength_calc == SAMPLE_WAVELENGTH


# Make sure we set up the forward/inverse to use the right methods
@using_fake_epics_pv
def test_ccm_calc():
    logger.debug('test_ccm_calc')
    calc = ccm.CCMCalc('TEST', name='calc')
    calc.alio.setpoint._read_pv.put(SAMPLE_ALIO)
    calc.alio.readback._read_pv.put(SAMPLE_ALIO)
    calc.wait_for_connection()

    theta = calc.theta.position
    theta_func = ccm.alio_to_theta(SAMPLE_ALIO, calc.gTheta0, calc.gR, calc.gD)
    assert theta == theta_func

    wavelength = calc.wavelength.position
    wavelength_func = ccm.theta_to_wavelength(theta, calc.gdspacing)
    assert wavelength == wavelength_func

    energy = calc.energy.position
    energy_func = ccm.wavelength_to_energy(energy)
    assert energy == energy_func

    calc.alio.setpoint._read_pv.put(0)
    calc.alio.readback._read_pv.put(0)

    calc.move(energy, wait=True)
    assert calc.alio.setpoint._read_pv.get() == SAMPLE_ALIO


# Make sure sync'd axes work and that unk/in/out states work
@using_fake_epics_pv
def test_ccm_main():
    tst_ccm = ccm.CCM(x_down='X:DOWN', x_up='X:UP', y_down='Y:DOWN',
                      y_up_north='Y:UPN', y_up_south='Y:UPS', alio='CC:ALIO',
                      theta2fine='CC:TH', inpos=8, outpos=0, name='tst_ccm')
    tst_ccm.x.down.user_readback._read_pv.put(0)
    tst_ccm.x.up.user_readback._read_pv.put(0)
    tst_ccm.x.down.user_setpoint._write_pv.put(0)
    tst_ccm.x.up.user_setpoint._write_pv.put(0)
    tst_ccm.y.down.user_setpoint._write_pv.put(0)
    tst_ccm.y.up_north.user_setpoint._write_pv.put(0)
    tst_ccm.y.up_south.user_setpoint._write_pv.put(0)
    tst_ccm.wait_for_connection()

    tst_ccm.y.move(5)
    assert tst_ccm.y.down.user_setpoint._write_pv.get() == 5
    assert tst_ccm.y.up_north.user_setpoint._write_pv.get() == 5
    assert tst_ccm.y.up_south.user_setpoint._write_pv.get() == 5

    assert tst_ccm.position == 'OUT'
    assert tst_ccm.removed
    assert not tst_ccm.inserted

    tst_ccm.x.down.user_readback._read_pv.put(8)
    tst_ccm.x.up.user_readback._read_pv.put(8)
    assert tst_ccm.position == 'IN'
    assert not tst_ccm.removed
    assert tst_ccm.inserted

    tst_ccm.x.down.user_readback._read_pv.put(4)
    tst_ccm.x.up.user_readback._read_pv.put(4)
    assert tst_ccm.position == 'Unknown'
    assert not tst_ccm.removed
    assert not tst_ccm.inserted

    tst_ccm.insert()
    assert tst_ccm.x.down.user_setpoint._write_pv.get() == 8
    assert tst_ccm.x.up.user_setpoint._write_pv.get() == 8

    tst_ccm.remove()
    assert tst_ccm.x.down.user_setpoint._write_pv.get() == 0
    assert tst_ccm.x.up.user_setpoint._write_pv.get() == 0
