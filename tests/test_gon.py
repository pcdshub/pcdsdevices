import logging
import numpy as np
import pytest
from ophyd.sim import make_fake_device
from unittest.mock import patch

from pcdsdevices.gon import (BaseGon, Goniometer, GonWithDetArm, Kappa, SamPhi,
                             XYZStage, SimKappa)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_kappa():
    FakeKappa = make_fake_device(SimKappa)
    fake_kap = FakeKappa(name='test', prefix_x='x', prefix_y='y', prefix_z='z',
                         prefix_eta='eta', prefix_kappa='kappa',
                         prefix_phi='phi', eta_max_step=2, kappa_max_step=2,
                         phi_max_step=2, kappa_ang=50)
    # set current positions
    fake_kap.eta.move(10)
    fake_kap.kappa.move(20)
    fake_kap.phi.move(30)

    return fake_kap


def test_gon_factory():
    logger.debug('test_gon_factory')
    assert isinstance(Goniometer(name='gon', prefix_hor='a', prefix_ver='b',
                                 prefix_rot='c', prefix_tip='d',
                                 prefix_tilt='e'), BaseGon)
    assert isinstance(Goniometer(name='gon', prefix_hor='a', prefix_ver='b',
                                 prefix_rot='c', prefix_tip='d',
                                 prefix_tilt='e', prefix_detver='i',
                                 prefix_dettilt='j', prefix_2theta='k'),
                      GonWithDetArm)


@pytest.mark.timeout(5)
def test_gon_init():
    logger.debug('test_gon_init')
    FakeGon = make_fake_device(BaseGon)
    FakeGon(name='test', prefix_hor='hor', prefix_ver='ver',
            prefix_rot='rot', prefix_tip='tip', prefix_tilt='tilt')
    FakeGon = make_fake_device(GonWithDetArm)
    FakeGon(name='test', prefix_hor='hor', prefix_ver='ver',
            prefix_rot='rot', prefix_tip='tip', prefix_tilt='tilt',
            prefix_detver='detver', prefix_dettilt='dettilt',
            prefix_2theta='2theta')
    FakeGon = make_fake_device(XYZStage)
    FakeGon(name='test', prefix_x='x', prefix_y='y', prefix_z='z')
    FakeGon = make_fake_device(SamPhi)
    FakeGon(name='test', prefix_samz='samz', prefix_samphi='samphi')
    FakeGon = make_fake_device(Kappa)
    FakeGon(name='test', prefix_x='x', prefix_y='y', prefix_z='z',
            prefix_eta='eta', prefix_kappa='kappa', prefix_phi='phi')


@pytest.mark.timeout(5)
def test_gon_disconnected():
    logger.debug('test_gon_disconnected')
    BaseGon(name='test1', prefix_hor='hor', prefix_ver='ver',
            prefix_rot='rot', prefix_tip='tip', prefix_tilt='tilt')
    GonWithDetArm(name='test2', prefix_hor='hor', prefix_ver='ver',
                  prefix_rot='rot', prefix_tip='tip', prefix_tilt='tilt',
                  prefix_detver='detver', prefix_dettilt='dettilt',
                  prefix_2theta='2theta')
    XYZStage(name='test3', prefix_x='x', prefix_y='y', prefix_z='z')
    SamPhi(name='test4', prefix_samz='samz', prefix_samphi='samphi')
    Kappa(name='test5', prefix_x='x', prefix_y='y', prefix_z='z',
          prefix_eta='eta', prefix_kappa='kappa', prefix_phi='phi')


def test_k_to_e(fake_kappa):
    # expected result based on old code
    expected_res = (-27.51268029508058, 10.713563480515766, 41.48731970491941)
    result = fake_kappa.k_to_e(eta=23, kappa=14, phi=46)
    assert np.isclose(expected_res, result).all()
    # test with constructor's params
    expected_res = (-16.46635439427449, 15.28854011258886, -36.4663543942744)
    result = fake_kappa.k_to_e()
    assert np.isclose(expected_res, result).all()


def test_e_to_k(fake_kappa):
    # expected result based on old code
    expected_res = (-28.9135906952099, 18.3080599808285, -51.9135906952099)
    result = fake_kappa.e_to_k(e_eta=23, e_chi=14, e_phi=46)
    assert np.isclose(expected_res, result).all()
    # test with constructor's params
    # when positions are: eat = 10, kappa = 20, phi = 30, angle = 50
    # the coordinates are:
    # (-16.466354394274497, 15.288540112588864, -36.46635439427449)
    expected_res = (10, 20, 30)
    result = fake_kappa.e_to_k()
    assert np.isclose(expected_res, result).all()


def test_forward(fake_kappa):
    # result that current positions for fake_kappa would give us
    forward = fake_kappa.forward(e_eta=-16.466354394274497,
                                 e_chi=15.288540112588864,
                                 e_phi=-36.46635439427449)
    # original position: eta=10, kappa=20, phi=30
    assert np.isclose(forward.eta, 10)
    assert np.isclose(forward.kappa, 20)
    assert np.isclose(forward.phi, 30)


def test_inverse(fake_kappa):
    inverse = fake_kappa.inverse(eta=10, kappa=20, phi=-30)
    # original pseudo coord: eta=-16.466354394274497, kappa=15.288540112588864,
    # phi=-36.46635439427449
    assert np.isclose(inverse.e_eta, -16.466354394274497)
    assert np.isclose(inverse.e_chi, 15.288540112588864)
    assert np.isclose(inverse.e_phi, -36.46635439427449)


def test_positions(fake_kappa):
    # current positions
    assert fake_kappa.eta.position == 10
    assert fake_kappa.kappa.position == 20
    assert fake_kappa.phi.position == 30
    # change positions
    fake_kappa.eta.move(11)
    fake_kappa.kappa.move(22)
    fake_kappa.phi.move(33)
    # new positions
    assert fake_kappa.eta.position == 11
    assert fake_kappa.kappa.position == 22
    assert fake_kappa.phi.position == 33


def test_coordinates(fake_kappa):
    # current pos:
    # eta = 10, kappa = 20, phi = 30, angle = 50
    # spherical coordinates:
    #      e_eta                 e_chi               e_phi
    # (-16.466354394274497, 15.288540112588864, -36.46635439427449)
    assert np.isclose(fake_kappa.e_eta_coord, -16.466354394274497)
    assert np.isclose(fake_kappa.e_chi_coord, 15.288540112588864)
    assert np.isclose(fake_kappa.e_phi_coord, -36.46635439427449)
    # new pos:
    # eta = 11, kappa = 22, phi = 33, angle = 50
    # spherical coordinates:
    #      e_eta                 e_chi               e_phi
    # (-18.121927886338778, 16.809862422228026, -40.12192788633878)
    fake_kappa.eta.move(11)
    fake_kappa.kappa.move(22)
    fake_kappa.phi.move(33)
    assert np.isclose(fake_kappa.e_eta_coord, -18.121927886338778)
    assert np.isclose(fake_kappa.e_chi_coord, 16.809862422228026)
    assert np.isclose(fake_kappa.e_phi_coord, -40.12192788633878)


def test_check_motor_step(fake_kappa):
    # max steps: 2, 2, 2
    # current positions: 10, 20, 30
    # numbers in range
    res = fake_kappa.check_motor_step(9, 19, 29)
    assert res is True
    # numbers outside the range - yes
    with patch('builtins.input', return_value='y'):
        res = fake_kappa.check_motor_step(5, 14, 23)
    assert res is True
    # numbers outside the range - no
    with patch('builtins.input', return_value='n'):
        res = fake_kappa.check_motor_step(5, 14, 23)
    assert res is False


def test_moving(fake_kappa):
    eta_pos, kappa_pos, phi_pos = fake_kappa.e_to_k(e_eta=3, e_chi=5, e_phi=7)
    fake_kappa.e_eta.mv(3)
    fake_kappa.e_chi.mv(5)
    fake_kappa.e_phi.mv(7)
    assert fake_kappa.eta.position == eta_pos
    assert fake_kappa.kappa.position == kappa_pos
    assert fake_kappa.phi.position == phi_pos


def test_mv_e_eta(fake_kappa):
    eta_pos = fake_kappa.e_to_k(e_eta=3)[0]
    with patch('pcdsdevices.gon.Kappa.check_motor_step', return_value=True):
        fake_kappa.mv_e_eta(value=3)
        assert fake_kappa.eta.position == eta_pos


def test_mv_e_chi(fake_kappa):
    kappa_pos = fake_kappa.e_to_k(e_chi=5)[1]
    with patch('pcdsdevices.gon.Kappa.check_motor_step', return_value=True):
        fake_kappa.mv_e_chi(value=5)
        assert fake_kappa.kappa.position == kappa_pos


def test_mv_e_phi(fake_kappa):
    phi_pos = fake_kappa.e_to_k(e_phi=7)[2]
    with patch('pcdsdevices.gon.Kappa.check_motor_step', return_value=True):
        fake_kappa.mv_e_phi(value=7)
        assert fake_kappa.phi.position == phi_pos
