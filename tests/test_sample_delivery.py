import logging

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.sample_delivery import (HPLC, CoolerShaker, FlowIntegrator,
                                         PressureController, Selector)

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_sds_init():
    logger.debug('test_sds_init')
    FakeFlowIntegrator = make_fake_device(FlowIntegrator)
    FakeFlowIntegrator('FAKE:FI', name='test_fi',
                       integrator_source_prefix='test1',
                       flow_source_prefix='test2', names_prefix='test3',
                       start1_prefix='test4', used1_prefix='test5',
                       time1_prefix='test6', start2_prefix='test7',
                       used2_prefix='test8', time2_prefix='test9',
                       start3_prefix='test10', used3_prefix='test11',
                       time3_prefix='test12', start4_prefix='test13',
                       used4_prefix='test14', time4_prefix='test15',
                       start5_prefix='test16', used5_prefix='test17',
                       time5_prefix='test18', start6_prefix='test19',
                       used6_prefix='test20', time6_prefix='test21',
                       start7_prefix='test22', used7_prefix='test23',
                       time7_prefix='test24', start8_prefix='test25',
                       used8_prefix='test26', time8_prefix='test27',
                       start9_prefix='test28', used9_prefix='test29',
                       time9_prefix='test30', start10_prefix='test31',
                       used10_prefix='test32', time10_prefix='test33')
    FakePressureController = make_fake_device(PressureController)
    FakePressureController('FAKE:PCM', name='test_pcm', status_prefix='test34',
                           pressure1_prefix='test35', enabled1_prefix='test36',
                           limit1_prefix='test37', SP1_prefix='test38',
                           pressure2_prefix='test39', enabled2_prefix='test40',
                           limit2_prefix='test41', SP2_prefix='test42')
    FakeHPLC = make_fake_device(HPLC)
    FakeHPLC('FAKE:HPLC', name='test_hplc', status_prefix='test43',
             run_prefix='test44', flowrate_prefix='test45',
             set_flowrate_prefix='test46', flowrate_SP_prefix='test47',
             pressure_prefix='test48', pressure_units_prefix='test49',
             set_max_pressure_prefix='test50', max_pressure_prefix='test51',
             clear_error_prefix='test52')
    FakeCoolerShaker = make_fake_device(CoolerShaker)
    FakeCoolerShaker('FAKE:CS', name='test_cs', temperature1_prefix='test53',
                     SP1_prefix='test54', set_SP1_prefix='test55',
                     current1_prefix='test56', temperature2_prefix='test57',
                     SP2_prefix='test58', set_SP2_prefix='test59',
                     current2_prefix='test60', reboot_prefix='test61')
    FakeSelector = make_fake_device(Selector)
    FakeSelector('FAKE:SEL', name='test_sel', remote_control_prefix='test62',
                 status_prefix='test63', flow_prefix='test64',
                 flowstate_prefix='test65', flowtype_prefix='test66',
                 FM_rb_prefix='test67', FM_reset_prefix='test68',
                 FM_prefix='test69', names_button_prefix='test70',
                 couple_button_prefix='test71', names1_prefix='test72',
                 names2_prefix='test73', shaker1_prefix='test74',
                 shaker2_prefix='test75', shaker3_prefix='test76',
                 shaker4_prefix='test77')


@pytest.mark.timeout(5)
def test_sds_disconnected():
    logger.debug('test_sds_disconnected')
    FlowIntegrator('FAKE:FI', name='test_fi', integrator_source_prefix='test1',
                   flow_source_prefix='test2', names_prefix='test3',
                   start1_prefix='test4', used1_prefix='test5',
                   time1_prefix='test6', start2_prefix='test7',
                   used2_prefix='test8', time2_prefix='test9',
                   start3_prefix='test10', used3_prefix='test11',
                   time3_prefix='test12', start4_prefix='test13',
                   used4_prefix='test14', time4_prefix='test15',
                   start5_prefix='test16', used5_prefix='test17',
                   time5_prefix='test18', start6_prefix='test19',
                   used6_prefix='test20', time6_prefix='test21',
                   start7_prefix='test22', used7_prefix='test23',
                   time7_prefix='test24', start8_prefix='test25',
                   used8_prefix='test26', time8_prefix='test27',
                   start9_prefix='test28', used9_prefix='test29',
                   time9_prefix='test30', start10_prefix='test31',
                   used10_prefix='test32', time10_prefix='test33')
    PressureController('FAKE:PCM', name='test_pcm', status_prefix='test34',
                       pressure1_prefix='test35', enabled1_prefix='test36',
                       limit1_prefix='test37', SP1_prefix='test38',
                       pressure2_prefix='test39', enabled2_prefix='test40',
                       limit2_prefix='test41', SP2_prefix='test42')
    HPLC('FAKE:HPLC', name='test_hplc', status_prefix='test43',
         run_prefix='test44', flowrate_prefix='test45',
         set_flowrate_prefix='test46', flowrate_SP_prefix='test47',
         pressure_prefix='test48', pressure_units_prefix='test49',
         set_max_pressure_prefix='test50', max_pressure_prefix='test51',
         clear_error_prefix='test52')
    CoolerShaker('FAKE:CS', name='test_cs', temperature1_prefix='test53',
                 SP1_prefix='test54', set_SP1_prefix='test55',
                 current1_prefix='test56', temperature2_prefix='test57',
                 SP2_prefix='test58', set_SP2_prefix='test59',
                 current2_prefix='test60', reboot_prefix='test61')
    Selector('FAKE:SEL', name='test_sel', remote_control_prefix='test62',
             status_prefix='test63', flow_prefix='test64',
             flowstate_prefix='test65', flowtype_prefix='test66',
             FM_rb_prefix='test67', FM_reset_prefix='test68',
             FM_prefix='test69', names_button_prefix='test70',
             couple_button_prefix='test71', names1_prefix='test72',
             names2_prefix='test73', shaker1_prefix='test74',
             shaker2_prefix='test75', shaker3_prefix='test76',
             shaker4_prefix='test77')
