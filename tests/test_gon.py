import logging

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.gon import (BaseGon, Goniometer, GonWithDetArm, Kappa, SamPhi,
                             XYZStage)

logger = logging.getLogger(__name__)


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
